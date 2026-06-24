"""
Adapter FinancePort — retenciones, percepciones, caja y reportes
(agente de Contabilidad/Finanzas).

Endpoints reales (openapi.yaml):
  POST /api/retentions          -> create_retention()   (interrupt — capa de tools)
  POST /api/perceptions         -> create_perception()  (interrupt — capa de tools)
  POST /api/cash/open           -> open_cash()           (interrupt — capa de tools)
  GET  /api/cash/close/{cash}   -> close_cash()          (interrupt — capa de tools)
  GET  /api/report              -> get_daily_report()
  POST /api/reports/general-sale -> get_general_sale_report()

OPEN RISK RESOLVED (Phase 2 follow-up, real source-code read — the prior
Phase-2 pass only confirmed SOME nested structure was required via live
500s; this pass traced the exact shape and found retentions and perceptions
are NOT identical, correcting the prior assumption):

- create_retention(): RetentionTransform::transform()
  (app/CoreFacturalo/Requests/Api/Transform/RetentionTransform.php:23-24)
  requires BOTH `datos_del_emisor` (-> EstablishmentTransform.php:10, a bare
  `{"code": "<Establishment.code>"}`) AND `datos_del_proveedor` (->
  Common/PersonTransform.php:12-21 — `codigo_tipo_documento_identidad`/
  `numero_documento`/`apellidos_y_nombres_o_razon_social` required,
  `ubigeo`/`direccion`/`correo_electronico`/`telefono` optional).
  RetentionValidation::validation() (Api/Validation/RetentionValidation.php:
  9-15) resolves both server-side via Functions::establishment()/
  Functions::person() — confirmed via direct source read, not guessed.
- create_perception(): PerceptionTransform::transform()
  (PerceptionTransform.php:23, the `establishment` line is COMMENTED OUT in
  the real source) and PerceptionValidation::validation()
  (PerceptionValidation.php:9, hardcodes `auth()->user()->establishment_id`
  server-side) BOTH confirm perceptions do NOT need `datos_del_emisor` at
  all — only `datos_del_cliente_o_receptor` (same PersonTransform shape,
  customer not supplier). Sending `datos_del_emisor` for a perception is
  harmless (ignored) but unnecessary.

OPEN RISK PARTIALLY RESOLVED for create_retention() (one additional real
attempt, per the dispatch fix's same root cause): like dispatch's customer
identity, datos_del_proveedor ALSO needs codigo_pais explicitly
(persons.country_id is NOT NULL, Functions::valueKeyInArray() defaults
missing keys to null) -- callers must build supplier_identity with
codigo_pais set (e.g. "PE").
GENUINELY UNRESOLVED (time-boxed, NOT chased further): with a minimal
totales-only retention body and no documentos (referenced underlying
purchase invoices being retained against), a real attempt hit
UpstreamError: Invalid argument supplied for foreach() deep inside
document/XML generation (Facturalo->save(), not reached via source read in
this pass -- both RetentionTransform::document() and RetentionInput::
document() guard their foreach with key_exists()/array_key_exists(), so the
unguarded foreach is further downstream). This is consistent with a
retention being a SUNAT document that conceptually MUST reference at least
one real purchase invoice -- Phase 3 tool design for crear_retencion should
treat documentos (per-document RUC/series/number/totals, matching
RetentionTransform::document()'s shape) as effectively required, not
optional, and resolve it from an existing Purchase record before calling
this adapter.

"""
from __future__ import annotations

from typing import Any, Dict

from adapters.facturadorpro7_api.http_client import FacturadorPro7Client
from core.domain import Cash, Perception, Report, Retention
from core.ports import FinancePort


class FinanceAdapter(FinancePort):
    def __init__(self, client: FacturadorPro7Client):
        self._client = client

    async def create_retention(
        self,
        d: Dict[str, Any],
        *,
        establishment_fiscal_code: str,
        supplier_identity: Dict[str, Any],
    ) -> Retention:  # interrupt (tools layer)
        payload: Dict[str, Any] = {
            **d,
            "datos_del_emisor": {"codigo_del_domicilio_fiscal": establishment_fiscal_code},
            "datos_del_proveedor": supplier_identity,
        }
        result = await self._client.post("/api/retentions", json=payload)
        raw = (result or {}).get("data") or {}
        return Retention(id=raw.get("id", 0), amount=float(d.get("totales", {}).get("total", 0) or 0), extra=raw)

    async def create_perception(
        self, d: Dict[str, Any], *, customer_identity: Dict[str, Any]
    ) -> Perception:  # interrupt (tools layer)
        payload: Dict[str, Any] = {**d, "datos_del_cliente_o_receptor": customer_identity}
        result = await self._client.post("/api/perceptions", json=payload)
        raw = (result or {}).get("data") or {}
        return Perception(id=raw.get("id", 0), amount=float(d.get("totales", {}).get("total", 0) or 0), extra=raw)

    async def open_cash(self, d: Dict[str, Any]) -> Cash:  # interrupt (tools layer)
        # NOTE: openapi.yaml lists no `required` array for this endpoint at
        # all. Live discovery (real 422 against the sandbox) confirmed
        # beginning_balance IS required, and — contrary to the plan's
        # assumption — date_opening/time_opening are NOT actually required
        # by this tenant's validation (a bare {"beginning_balance": X}
        # succeeded with 200). Caller-provided extra fields (user_id,
        # date_opening, time_opening, reference_number) are still passed
        # through for tenants/configs where they ARE required.
        payload: Dict[str, Any] = {"beginning_balance": d.get("beginning_balance", 0), **d}
        result = await self._client.post("/api/cash/open", json=payload)
        cash_id = (result or {}).get("data", {}).get("cash_id", 0)
        return Cash(id=cash_id, state=True, beginning_balance=float(payload["beginning_balance"]))

    async def close_cash(self, cash_id: int) -> Cash:  # interrupt (tools layer)
        # NOTE: openapi.yaml documents this as GET, not POST — confirmed
        # live (a POST to this path is not even routed; GET succeeds with
        # 200 and no request body). The design.md port comment said
        # "POST /api/cash/close/{cash}" but the real spec/route is GET.
        await self._client.get(f"/api/cash/close/{cash_id}")
        return Cash(id=cash_id, state=False, beginning_balance=0.0)

    async def get_daily_report(self, **filters: Any) -> Report:
        result = await self._client.get("/api/report", params=filters or None)
        return Report(data=(result or {}).get("data", {}))

    async def get_general_sale_report(self, d: Dict[str, Any]) -> Report:
        # NOTE: openapi.yaml documents date_start/date_end/establishment_id
        # as the (optional, no `required` listed) body. Live discovery (two
        # rounds of real 422s against the sandbox) revealed this tenant's
        # actual validation ALSO requires period/month_start/month_end IN
        # ADDITION to date_start/date_end — both sets together, not either/or.
        payload: Dict[str, Any] = dict(d)
        if "period" not in payload and "date_start" in payload:
            year = int(str(payload["date_start"])[:4])
            month = int(str(payload["date_start"])[5:7])
            payload.setdefault("period", year)
            payload.setdefault("month_start", month)
            payload.setdefault("month_end", month)
        result = await self._client.post("/api/reports/general-sale", json=payload)
        return Report(data=(result or {}).get("data", {}))

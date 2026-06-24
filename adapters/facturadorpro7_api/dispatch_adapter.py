"""
Adapter DispatchPort — guías de remisión (despacho), agente de Logística.

Endpoints reales (openapi.yaml):
  GET  /api/dispatches/tables  -> get_tables()
  POST /api/dispatches         -> create_dispatch()  (borrador, NO interrupt)
  POST /api/dispatches/send    -> send_dispatch()    (interrupt — capa de tools)
  GET  /api/dispatches/records -> list_dispatches()

OPEN RISK PARTIALLY RESOLVED (Phase 2 follow-up, real source-code read of
DispatchTransform.php/DispatchInput.php/DispatchValidation.php): the
datos_del_emisor + origin/delivery ubigeo fix below is necessary and
verified to get PAST the original "datos_del_emisor" gap — a real attempt
progressed through series validation and customer-person resolution after
two additional fixes discovered live:
  1. The Transform layer reads Spanish API field names (`serie_documento`/
     `numero_documento`, not `series`/`number`) — caller drafts must use
     the `*_documento` naming, matching openapi.yaml's documented fields
     for OTHER endpoints (sale-note's generate-cpe uses the same naming).
  2. `datos_del_cliente_o_receptor`/`datos_del_proveedor` (PersonTransform)
     need `codigo_pais` explicitly — Functions::valueKeyInArray() defaults
     missing keys to `null`, and `persons.country_id` is NOT NULL.
GENUINELY UNRESOLVED (time-boxed per instruction, NOT chased further): BOTH
transport modes require an undocumented nested person object, not just one:
  - `transport_mode_type_id == "02"` (transporte privado) needs
    `DispatchInput::getDriverId()` (DispatchInput.php:462-486) -> a FULL
    `driver` object (`identity_document_type_id`/`number`/`name`/`license`/
    `telephone`) to firstOrCreate a `drivers` row.
  - `transport_mode_type_id == "01"` (transporte público) needs
    `DispatchInput::getDispatcherId()` (DispatchInput.php:410-427) -> a FULL
    `dispatcher` (transportista) object (`identity_document_type_id`/
    `number`/`name`/`number_mtc`) to firstOrCreate a `dispatchers` row —
    confirmed via a real attempt with `transport_mode_type_id="01"` that
    still 500s on `dispatchers.identity_document_type_id cannot be null`.
Neither requirement is in openapi.yaml or surfaced as an explicit port
parameter. No orphaned record was left in either case (confirmed live via
GET /api/dispatches/records — the dispatcher/driver insert failure happens
before any `dispatches` row is created). Phase 3 tool design for
`crear_guia_remision` must resolve dispatcher OR driver+vehicle data
(depending on the chosen transport mode) before calling this adapter — there
is no transport mode that skips a nested person requirement.
"""
from __future__ import annotations

from typing import Any, Dict, List

from adapters.facturadorpro7_api.http_client import FacturadorPro7Client
from core.domain import Dispatch, DispatchTables
from core.ports import DispatchPort


class DispatchAdapter(DispatchPort):
    def __init__(self, client: FacturadorPro7Client):
        self._client = client

    async def get_tables(self) -> DispatchTables:
        result = await self._client.get("/api/dispatches/tables") or {}
        transfer_reasons = result.get("transferReasonTypes", [])
        transport_modes = result.get("transportModeTypes", [])
        extra = {k: v for k, v in result.items() if k not in ("transferReasonTypes", "transportModeTypes")}
        return DispatchTables(transfer_reasons=transfer_reasons, transport_modes=transport_modes, extra=extra)

    async def create_dispatch(
        self,
        draft: Dict[str, Any],
        *,
        establishment_fiscal_code: str,
        origin_location_id: str,
        delivery_location_id: str,
    ) -> Dispatch:
        # OPEN RISK RESOLVED (Phase 2 follow-up, real source-code read of
        # DispatchTransform.php:25 + DispatchValidation.php:12 +
        # DispatchInput.php:158-198): the real pipeline requires
        # `datos_del_emisor: {"codigo_del_domicilio_fiscal": <Establishment.
        # code>}` (resolved server-side to establishment_id via
        # Functions::establishment()) PLUS a 6-digit ubigeo `location_id`
        # nested inside BOTH `direccion_partida` (origin) and
        # `direccion_llegada` (delivery) — none of this is in openapi.yaml
        # or validated by DispatchController::store() (which only checks
        # delivery.address/origin.address), so it fails downstream in the
        # Transform/Input layers instead of with a clean 422. We build the
        # full required shape here; the caller's draft (delivery/origin
        # addresses, items, transfer reason, transport mode, etc., resolved
        # via get_tables() first) is layered underneath via the "extra: dict"
        # escape exactly as before.
        delivery = dict(draft.get("delivery") or {})
        origin = dict(draft.get("origin") or {})
        delivery.setdefault("location_id", delivery_location_id)
        origin.setdefault("location_id", origin_location_id)

        payload: Dict[str, Any] = {
            **draft,
            "datos_del_emisor": {"codigo_del_domicilio_fiscal": establishment_fiscal_code},
            "direccion_partida": {
                "ubigeo": origin.get("location_id", origin_location_id),
                "direccion": origin.get("address", ""),
                "codigo_del_domicilio_fiscal": establishment_fiscal_code,
            },
            "direccion_llegada": {
                "ubigeo": delivery.get("location_id", delivery_location_id),
                "direccion": delivery.get("address", ""),
                "codigo_del_domicilio_fiscal": establishment_fiscal_code,
            },
            "delivery": delivery,
            "origin": origin,
        }
        result = await self._client.post("/api/dispatches", json=payload)
        raw = result.get("data") or {}
        return Dispatch(
            id=raw.get("id", 0),
            origin_address=origin.get("address", ""),
            delivery_address=delivery.get("address", ""),
            state=None,
            sunat_status=None,
            extra={"external_id": raw.get("external_id"), "number": raw.get("number")},
        )

    async def send_dispatch(self, id: int) -> Dispatch:  # interrupt (tools layer)
        # /api/dispatches/send takes external_id, not the numeric id — the
        # tool layer is expected to have the Dispatch entity (with its
        # extra["external_id"]) from create_dispatch(); the port signature
        # takes `id` as the canonical identifier per design.md, so callers
        # must pass the dispatch's numeric id and we resolve external_id by
        # listing records first (no GET-by-id endpoint exists for dispatch).
        dispatches = await self.list_dispatches()
        match = next((d for d in dispatches if d.id == id), None)
        external_id = match.extra.get("external_id") if match else None
        if not external_id:
            raise ValueError(f"No se encontró el external_id de la guía con id={id}; no se puede enviar a SUNAT.")
        result = await self._client.post("/api/dispatches/send", json={"external_id": external_id})
        return Dispatch(
            id=id,
            origin_address=match.origin_address if match else "",
            delivery_address=match.delivery_address if match else "",
            state=(result or {}).get("state_type_id"),
            sunat_status=(result or {}).get("state_type_description"),
            extra={"external_id": external_id},
        )

    async def list_dispatches(self, **filters: Any) -> List[Dispatch]:
        result = await self._client.get("/api/dispatches/records", params=filters or None)
        raw_list = self._unwrap_list(result)
        return [self._to_dispatch(raw) for raw in raw_list]

    @staticmethod
    def _unwrap_list(result: Any) -> List[Dict[str, Any]]:
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            data = result.get("data")
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                inner = data.get("data")
                if isinstance(inner, list):
                    return inner
        return []

    @staticmethod
    def _to_dispatch(raw: dict) -> Dispatch:
        # NOTE: GET /api/dispatches/records (list view, real shape verified
        # live) does NOT echo origin/delivery addresses — it's a summary row
        # (customer, state, document links) rather than the create-response
        # shape. origin_address/delivery_address are left empty here; the
        # full addresses are only available right after create_dispatch().
        origin = raw.get("origin") if isinstance(raw.get("origin"), dict) else {}
        delivery = raw.get("delivery") if isinstance(raw.get("delivery"), dict) else {}
        return Dispatch(
            id=raw.get("id", 0),
            origin_address=origin.get("address", ""),
            delivery_address=delivery.get("address", ""),
            state=raw.get("state_type_id"),
            sunat_status=raw.get("state_type_description"),
            extra={
                "external_id": raw.get("external_id"),
                "number": raw.get("number"),
                "customer_name": raw.get("customer_name"),
                "btn_send": raw.get("btn_send"),
            },
        )

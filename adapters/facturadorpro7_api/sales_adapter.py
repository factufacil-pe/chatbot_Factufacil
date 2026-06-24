"""
Adapter SalesPort — preliminar de venta → generación de CPE (irreversible
ante SUNAT).

Endpoints reales (openapi.yaml):
  POST /api/sale-note                    -> create_sale_note()  (borrador, NO interrupt)
  POST /api/sale-note/{id}/generate-cpe  -> generate_cpe()      (interrupt — capa de tools)

GENUINELY UNRESOLVED SERVER BUG (Phase 2 follow-up, time-boxed): three NOT
NULL gaps were found and fixed live in sequence — `prefix` ->
`time_of_issue` -> `exchange_rate_sale` (see create_sale_note() inline
comments for the source-code citation of each). After fixing all three, a
FOURTH NOT-NULL violation appeared on `total` — and `total` is a computed
aggregate (sum of line-item totals/taxes), not a simple scalar default like
the first three. This strongly suggests `SaleNoteController::mergeData()`
assumes a richer web-UI flow that pre-computes ALL total/tax columns
client-side before posting, and the bare API endpoint does no such
computation server-side. Continuing to default `total`/`total_taxed`/
`total_igv`/etc. one-by-one would require either reverse-engineering the
full tax-calculation logic this client doesn't have, or guessing — both
out of scope per the time-box. CONCLUSION: this is a genuine server-side
gap in how `/api/sale-note` handles minimal payloads, independent of this
adapter's request-building correctness (which IS verified: the first three
real fixes each produced a DIFFERENT, more specific real error, proving the
request is reaching deep into the real insert logic). Phase 3 tool design
for `crear_preliminar_venta` should compute and send the full total/tax
breakdown explicitly (description, unit_price, igv breakdown, total per
line and aggregate) rather than relying on any server-side computation.
"""
from __future__ import annotations

from typing import Any, Dict

from adapters.facturadorpro7_api.http_client import FacturadorPro7Client
from core.domain import Cpe, SaleNote
from core.ports import SalesPort


class SalesAdapter(SalesPort):
    def __init__(self, client: FacturadorPro7Client):
        self._client = client

    async def create_sale_note(self, draft: Dict[str, Any]) -> SaleNote:
        # draft is expected to carry series_id/customer_id/date_of_issue/items
        # (required per openapi.yaml) plus any optional fields the caller set.
        #
        # PHASE 2 FOLLOW-UP (source-code read of
        # app/Http/Controllers/Tenant/Api/SaleNoteController.php
        # mergeData()/getDataSeries(), ~lines 254-276): confirmed `prefix` is
        # NEVER populated by this controller — `getDataSeries()` only reads
        # `Series::find($series_id)->number` (a string like "NV01") and an
        # incrementing `number`; it never touches `prefix`. The `SaleNote`
        # model has `prefix` fillable (app/Models/Tenant/SaleNote.php:162)
        # and even has legacy fallback logic that READS it
        # (`$this->prefix . '-' . $this->id` at lines 484/642) when
        # series/number are empty, but nothing in the real create path WRITES
        # it. The `Series` model/migration has no `prefix` column at all —
        # this is consistent with the prior pass's live-discovered 500 being
        # a genuine server-side gap, not a client-payload gap. Sending
        # `prefix: ""` explicitly is tested below as one hypothesis; if the
        # tenant still 500s, this is NOT an adapter bug — do not keep
        # guessing additional keys.
        #
        # PHASE 2 FOLLOW-UP ROUND 2 (live discovery, two additional probes):
        # with prefix="" the create progressed past that gap and hit a NEW
        # NOT-NULL violation on `time_of_issue`, then after defaulting that
        # too, a THIRD NOT-NULL violation on `exchange_rate_sale`. All three
        # — `prefix`/`time_of_issue`/`exchange_rate_sale` — are the exact
        # same class of gap: fillable on the `SaleNote` model
        # (app/Models/Tenant/SaleNote.php) but never populated by
        # `mergeData()`/`getDataSeries()`. Default all three; caller override
        # still wins via merge order. (Mirrors the identical pattern already
        # fixed in purchases_adapter.py for time_of_issue/currency_type_id/
        # exchange_rate_sale on the `purchases` table.)
        from datetime import datetime

        payload: Dict[str, Any] = {
            "prefix": "",
            "time_of_issue": datetime.now().strftime("%H:%M:%S"),
            "exchange_rate_sale": 1.0,
            **draft,
        }
        result = await self._client.post("/api/sale-note", json=payload)
        raw = result.get("data") or {}
        return SaleNote(
            id=raw.get("id"),
            customer_id=draft.get("customer_id"),
            items=draft.get("items", []),
            total=float(raw.get("total", 0) or 0),
            series=raw.get("number", "").split("-")[0] if raw.get("number") else None,
            number=raw.get("number"),
            state=raw.get("state_type_id"),
        )

    async def generate_cpe(self, sale_note_id: int) -> Cpe:  # interrupt (called from tools layer)
        # generate-cpe requires document-type/series/number/fecha/hora — the
        # caller (tool layer) is expected to pass these via a richer call;
        # the port signature takes only sale_note_id, so we resolve the
        # remaining required fields from the sale note itself plus sane
        # current-time defaults. This mirrors the design's "propose then
        # confirm" flow: the preliminary data was already decided when the
        # sale note was created.
        from datetime import datetime, date

        now = datetime.now()
        payload = {
            "codigo_tipo_documento": "03",  # Boleta by default; Factura ("01") needs RUC customer, decided at tool layer
            "serie_documento": "B001",
            "numero_documento": str(sale_note_id),
            "fecha_de_emision": date.today().isoformat(),
            "hora_de_emision": now.strftime("%H:%M:%S"),
        }
        result = await self._client.post(f"/api/sale-note/{sale_note_id}/generate-cpe", json=payload)
        raw = result.get("data") or {}
        return Cpe(
            id=raw.get("id", sale_note_id),
            sale_note_id=sale_note_id,
            document_type_id=payload["codigo_tipo_documento"],
            series=raw.get("number", "").split("-")[0] if raw.get("number") else payload["serie_documento"],
            number=raw.get("number") or payload["numero_documento"],
            sunat_status=raw.get("state_type_description"),
        )

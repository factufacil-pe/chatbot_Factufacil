"""
Adapter PurchasesPort — registro de una compra (interrupt — capa de tools).

Endpoint real (openapi.yaml):
  POST /api/purchases -> create_purchase()

OPEN RISK RESOLVED (Phase 2 follow-up, real source-code read of
modules/Purchase/Http/Controllers/Api/PurchaseController.php): `store()`
calls `self::convert($request)` (fills user_id/establishment_id/supplier/
soap_type_id/group_id/state_type_id only) then `$doc->items()->create($row)`
directly for each item in `$data['items']` — NO Transform/Input class fills
defaults for line items here, unlike sale-note/dispatch. The
`purchase_items` table has a NOT-NULL `item` json column
(database/migrations/tenant/2019_02_12_000005_tenant_purchase_items_table.php
line 21) that nothing populates server-side. Each item dict in the request
MUST carry an `item` key (a product snapshot) or the INSERT violates the
NOT-NULL constraint with a 500 (confirmed live in the prior Phase-2 pass,
root cause confirmed here via source).

PHASE 2 FOLLOW-UP ROUND 2 (live, one additional real attempt): the item
snapshot fix above is necessary but not sufficient — a real attempt with a
partial snapshot (description/internal_id/unit_type_id/item_code/
item_code_gs1 only) progressed past the NOT-NULL error but then crashed
`createPdf()` (called OUTSIDE the DB transaction, AFTER commit — confirmed
by reading PurchaseController::store() lines 140-153 — so this does NOT
roll back the write) with `Undefined property: stdClass::$is_set`. The
`purchase_a4` PDF template reads `$item->is_set` off the stored JSON
snapshot — `Item.php:158` confirms `is_set` is a real Item model column the
template expects. Adding `is_set: False` as a default key (caller override
still wins) made a real end-to-end create_purchase() succeed live
(id=120, number=F001-999002, marked test data). `is_set` defaults to False
here because the agent layer only ever resolves simple, non-bundle items
via ItemsPort; true item-set/bundle purchases are out of scope for this
change.
"""
from __future__ import annotations

from typing import Any, Dict, List

from adapters.facturadorpro7_api.http_client import FacturadorPro7Client
from core.domain import Purchase
from core.ports import PurchasesPort


class PurchasesAdapter(PurchasesPort):
    def __init__(self, client: FacturadorPro7Client):
        self._client = client

    async def create_purchase(
        self, draft: Dict[str, Any], *, item_snapshots: List[Dict[str, Any]]
    ) -> Purchase:  # interrupt (tools layer)
        # NOTE: openapi.yaml documents document_type_id/series/number/
        # date_of_issue/supplier_id/items as required. Real 500s against the
        # sandbox tenant (non-null-constraint failures, discovered live, not
        # guessed) revealed this tenant's `purchases` table ALSO requires
        # time_of_issue, currency_type_id and exchange_rate_sale with no DB
        # default. Fill sane defaults when the caller's draft omits them;
        # the caller's explicit values always win (merge order below).
        from datetime import datetime

        items = [dict(row) for row in draft.get("items", [])]
        for idx, row in enumerate(items):
            if "item" not in row:
                snapshot = item_snapshots[idx] if idx < len(item_snapshots) else {}
                row["item"] = {"is_set": False, **snapshot}

        payload: Dict[str, Any] = {
            "time_of_issue": datetime.now().strftime("%H:%M:%S"),
            "currency_type_id": "PEN",
            "exchange_rate_sale": 1.0,
            **draft,
            "items": items,
        }
        result = await self._client.post("/api/purchases", json=payload)
        raw = result.get("data") or {}
        return Purchase(
            id=raw.get("id"),
            supplier_id=draft.get("supplier_id"),
            doc_type_id=draft.get("document_type_id", ""),
            series=draft.get("series", ""),
            number=raw.get("number_full") or draft.get("number", ""),
            date_of_issue=draft.get("date_of_issue", ""),
            items=items,
            total=float(draft.get("total", 0) or 0),
        )

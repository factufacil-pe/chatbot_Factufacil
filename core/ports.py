"""
Puertos (interfaces) del dominio.
El core solo habla con estas abstracciones — nunca con implementaciones concretas.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.domain import (
    Brand,
    Cash,
    ChatMessage,
    Category,
    Cpe,
    Customer,
    Dispatch,
    DispatchTables,
    Item,
    ItemDraft,
    Perception,
    Purchase,
    Report,
    RetrievedDocument,
    Retention,
    SaleNote,
    StockMovement,
    StockTxn,
    Supplier,
)


class LLMPort(ABC):
    """Puerto de salida — generación de texto."""

    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class RAGPort(ABC):
    """Puerto de salida — recuperación semántica de documentos."""

    @abstractmethod
    def retrieve(self, query: str, k: int = 4) -> List[RetrievedDocument]: ...

    @abstractmethod
    def reindex(self) -> None: ...

    @abstractmethod
    def get_stats(self) -> dict: ...


class MemoryPort(ABC):
    """Puerto de salida — memoria conversacional por sesión."""

    @abstractmethod
    def get_history(self, session_id: str) -> List[ChatMessage]: ...

    @abstractmethod
    def save_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None: ...

    @abstractmethod
    def clear(self, session_id: str) -> bool: ...

    @abstractmethod
    def get_session_info(self, session_id: str) -> dict: ...

    @abstractmethod
    def list_sessions(self) -> List[str]: ...


# ---------------------------------------------------------------------------
# Ports ERP (FacturadorPro7) — aditivos, co-piloto multiagente.
# Async: hacen I/O real contra una API remota (a diferencia de los 3 ports
# sync de arriba, que son locales). Cada uno se implementa en
# adapters/facturadorpro7_api/*. El core no importa LangGraph/LangChain ni
# httpx — solo conoce estas firmas.
# ---------------------------------------------------------------------------


class ItemsPort(ABC):
    """Búsqueda/creación liviana de productos — compartido por Compras y Ventas
    para el flujo inline "crear si no existe". El mantenimiento profundo de
    catálogo vive en InventoryPort (exclusivo del agente de Inventario)."""

    @abstractmethod
    async def search(self, query: str, *, by_barcode: bool = False, page: int = 1) -> List[Item]: ...

    @abstractmethod
    async def create(self, item: ItemDraft) -> Item: ...


class InventoryPort(ABC):
    """Mantenimiento profundo de catálogo y stock — exclusivo del agente de
    Inventario/Producto."""

    @abstractmethod
    async def get_item(self, id: int) -> Item: ...

    @abstractmethod
    async def update_item(self, id: int, patch: Dict[str, Any]) -> Item: ...

    @abstractmethod
    async def change_active(self, id: int, active: bool) -> None: ...

    @abstractmethod
    async def change_favorite(self, id: int, favorite: bool) -> None: ...

    @abstractmethod
    async def list_categories(self) -> List[Category]: ...

    @abstractmethod
    async def list_brands(self) -> List[Brand]: ...

    @abstractmethod
    async def register_transaction(self, txn: StockTxn) -> StockMovement: ...


class CustomersPort(ABC):
    """Búsqueda de clientes — agente de Ventas."""

    @abstractmethod
    async def search(self, query: str) -> List[Customer]: ...


class SuppliersPort(ABC):
    """Búsqueda de proveedores — agente de Compras."""

    @abstractmethod
    async def search(self, query: str) -> List[Supplier]: ...


class SalesPort(ABC):
    """Ventas: preliminar → generación de CPE (irreversible ante SUNAT)."""

    @abstractmethod
    async def create_sale_note(self, draft: Dict[str, Any]) -> SaleNote: ...

    @abstractmethod
    async def generate_cpe(self, sale_note_id: int) -> Cpe: ...  # interrupt


class PurchasesPort(ABC):
    """Compras: registro de una compra. Sin método de búsqueda propio — el
    agente de Compras inyecta SuppliersPort por separado.

    `item_snapshots` (additive, REQUIRED per-line): real source-code read of
    PurchaseController::store()/convert() (modules/Purchase/Http/Controllers/
    Api/PurchaseController.php) showed `$doc->items()->create($row)` is
    called directly off the caller's `items` payload — no server-side
    Transform/Input class fills defaults here, unlike sale-note/dispatch.
    `purchase_items.item` is a NOT-NULL json column
    (database/migrations/tenant/2019_02_12_000005_tenant_purchase_items_table.php
    line 21) that nothing populates if the caller omits it. The caller MUST
    supply one snapshot dict per line item (subset of: description,
    unit_type_id, internal_id, item_code, item_code_gs1, currency_type_id —
    whatever the agent/tool layer has from ItemsPort.search()/create()),
    keyed by the same index as `draft["items"]`."""

    @abstractmethod
    async def create_purchase(
        self, draft: Dict[str, Any], *, item_snapshots: List[Dict[str, Any]]
    ) -> Purchase: ...  # interrupt


class DispatchPort(ABC):
    """Logística: guías de remisión (despacho).

    `establishment_fiscal_code` and `location_id`s below are additive,
    REQUIRED params discovered via real source-code read (NOT in
    openapi.yaml at all):

    - `establishment_fiscal_code`: real pipeline is
      InputRequest::transformInputs() -> DispatchTransform::transform()
      (app/CoreFacturalo/Requests/Api/Transform/DispatchTransform.php:25)
      which builds `datos_del_emisor` into `establishment` via
      EstablishmentTransform (Common/EstablishmentTransform.php:10) — a
      bare `{"code": ...}`. Then DispatchValidation::validation()
      (Api/Validation/DispatchValidation.php:12) resolves that code to a
      numeric `establishment_id` via `Functions::establishment()`
      (Api/Validation/Functions.php:18-26), which looks up
      `Establishment::where('code', ...)`. The caller must supply the
      `Establishment.code` (e.g. "0000" for this tenant's main office, NOT
      a numeric id) — confirmed live via GET /api/company /
      GET /api/dispatches/tables.
    - `origin_location_id` / `delivery_location_id`: DispatchInput::origin()/
      delivery() (Requests/Inputs/DispatchInput.php:158-198) and
      DispatchTransform::origin()/delivery() (DispatchTransform.php:157-183)
      both require a 6-digit ubigeo (district) code inside the
      `direccion_partida`/`direccion_llegada` (origin/delivery) structures —
      absent from openapi.yaml entirely. No ubigeo-lookup endpoint exists in
      this API; the caller (tools layer) must supply it explicitly (e.g.
      resolved from a customer/establishment record), never hardcoded here.
    """

    @abstractmethod
    async def get_tables(self) -> DispatchTables: ...

    @abstractmethod
    async def create_dispatch(
        self,
        draft: Dict[str, Any],
        *,
        establishment_fiscal_code: str,
        origin_location_id: str,
        delivery_location_id: str,
    ) -> Dispatch: ...

    @abstractmethod
    async def send_dispatch(self, id: int) -> Dispatch: ...  # interrupt

    @abstractmethod
    async def list_dispatches(self, **filters: Any) -> List[Dispatch]: ...


class FinancePort(ABC):
    """Contabilidad/Finanzas: retenciones, percepciones, caja y reportes.

    `establishment_fiscal_code` / `supplier_identity` / `customer_identity`
    below are additive, REQUIRED params discovered via real source-code read
    (the prior Phase-2 pass only got as far as confirming SOME nested
    structure was required via live 500s; this pass traced the exact shape):

    - create_retention(): real pipeline is RetentionTransform::transform()
      (Api/Transform/RetentionTransform.php:23-24), which requires BOTH
      `datos_del_emisor` (-> EstablishmentTransform, same
      `{"code": "<Establishment.code>"}` shape as Dispatch above) AND
      `datos_del_proveedor` (-> PersonTransform, Common/PersonTransform.php:
      12-21 — needs `codigo_tipo_documento_identidad`, `numero_documento`,
      `apellidos_y_nombres_o_razon_social`; `ubigeo`/`direccion`/
      `correo_electronico`/`telefono` optional). Confirmed by
      RetentionValidation::validation() (Api/Validation/RetentionValidation.
      php:9-15) which resolves both via Functions::establishment()/
      Functions::person() server-side.
    - create_perception(): IMPORTANT CORRECTION vs the prior pass's
      documented open risk — PerceptionTransform::transform()
      (Api/Transform/PerceptionTransform.php:23, the `establishment` line is
      commented out in the actual source) and PerceptionValidation::
      validation() (Api/Validation/PerceptionValidation.php:9, hardcodes
      `auth()->user()->establishment_id`) BOTH show perceptions do NOT need
      `datos_del_emisor` at all — only `datos_del_cliente_o_receptor` (same
      PersonTransform shape as above, customer not supplier). The original
      Phase-2 "same gap as dispatches" note conflated retention and
      perception; they are NOT identical.
    """

    @abstractmethod
    async def create_retention(
        self,
        d: Dict[str, Any],
        *,
        establishment_fiscal_code: str,
        supplier_identity: Dict[str, Any],
    ) -> Retention: ...  # interrupt

    @abstractmethod
    async def create_perception(
        self, d: Dict[str, Any], *, customer_identity: Dict[str, Any]
    ) -> Perception: ...  # interrupt

    @abstractmethod
    async def open_cash(self, d: Dict[str, Any]) -> Cash: ...  # interrupt

    @abstractmethod
    async def close_cash(self, cash_id: int) -> Cash: ...  # interrupt

    @abstractmethod
    async def get_daily_report(self, **filters: Any) -> Report: ...

    @abstractmethod
    async def get_general_sale_report(self, d: Dict[str, Any]) -> Report: ...

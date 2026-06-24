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
    agente de Compras inyecta SuppliersPort por separado."""

    @abstractmethod
    async def create_purchase(self, draft: Dict[str, Any]) -> Purchase: ...  # interrupt


class DispatchPort(ABC):
    """Logística: guías de remisión (despacho)."""

    @abstractmethod
    async def get_tables(self) -> DispatchTables: ...

    @abstractmethod
    async def create_dispatch(self, draft: Dict[str, Any]) -> Dispatch: ...

    @abstractmethod
    async def send_dispatch(self, id: int) -> Dispatch: ...  # interrupt

    @abstractmethod
    async def list_dispatches(self, **filters: Any) -> List[Dispatch]: ...


class FinancePort(ABC):
    """Contabilidad/Finanzas: retenciones, percepciones, caja y reportes."""

    @abstractmethod
    async def create_retention(self, d: Dict[str, Any]) -> Retention: ...  # interrupt

    @abstractmethod
    async def create_perception(self, d: Dict[str, Any]) -> Perception: ...  # interrupt

    @abstractmethod
    async def open_cash(self, d: Dict[str, Any]) -> Cash: ...  # interrupt

    @abstractmethod
    async def close_cash(self, cash_id: int) -> Cash: ...  # interrupt

    @abstractmethod
    async def get_daily_report(self, **filters: Any) -> Report: ...

    @abstractmethod
    async def get_general_sale_report(self, d: Dict[str, Any]) -> Report: ...

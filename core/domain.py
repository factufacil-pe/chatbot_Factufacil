"""
Entidades del dominio. Sin dependencias externas — Python puro.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    role: str        # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievedDocument:
    content: str
    category: str
    topic: str


@dataclass
class ChatResponse:
    session_id: str
    answer: str
    sources: List[dict]
    message_count: int


@dataclass
class BotPersona:
    """Configuración de personalidad inyectable — permite múltiples bots."""
    name: str
    email: str
    phone: str
    system_prompt: str


# ---------------------------------------------------------------------------
# Entidades ERP (FacturadorPro7) — aditivas, co-piloto multiagente.
# Dataclasses livianas: el mapeo exacto de campos de la API real ocurre en
# los adapters (Fase 2). Aquí solo se define la forma mínima que necesitan
# los ports/agentes para razonar sobre el dominio.
# ---------------------------------------------------------------------------


@dataclass
class Item:
    """Producto/ítem del catálogo."""
    id: int
    description: str
    price: float
    barcode: Optional[str] = None
    has_igv: bool = True
    active: bool = True
    favorite: bool = False
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    stock: Optional[float] = None


@dataclass
class ItemDraft:
    """Datos para crear un nuevo ítem — sin id (todavía no existe)."""
    description: str
    price: float
    barcode: Optional[str] = None
    has_igv: bool = True
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image: Optional[str] = None


@dataclass
class Category:
    id: int
    name: str


@dataclass
class Brand:
    id: int
    name: str


@dataclass
class StockTxn:
    """Movimiento de stock a registrar (entrada/salida simple)."""
    item_code: str
    type: str  # "input" | "output"
    warehouse_id: int
    inventory_transaction_id: int
    quantity: float


@dataclass
class StockMovement:
    """Resultado de un movimiento de stock ya registrado."""
    id: int
    item_code: str
    type: str
    warehouse_id: int
    quantity: float
    resulting_stock: Optional[float] = None


@dataclass
class Customer:
    id: int
    document_number: str
    name: str
    address: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Supplier:
    id: int
    document_number: str
    name: str
    address: Optional[str] = None
    email: Optional[str] = None


@dataclass
class SaleNote:
    """Preliminar de venta (borrador, previo a generar CPE)."""
    id: int
    customer_id: int
    items: List[Dict[str, Any]] = field(default_factory=list)
    total: float = 0.0
    series: Optional[str] = None
    number: Optional[str] = None
    state: Optional[str] = None


@dataclass
class Cpe:
    """Comprobante de Pago Electrónico generado para SUNAT."""
    id: int
    sale_note_id: int
    document_type_id: str
    series: str
    number: str
    sunat_status: Optional[str] = None


@dataclass
class Purchase:
    id: int
    supplier_id: int
    doc_type_id: str
    series: str
    number: str
    date_of_issue: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    total: float = 0.0


@dataclass
class Dispatch:
    """Guía de remisión (despacho)."""
    id: int
    origin_address: str
    delivery_address: str
    state: Optional[str] = None
    sunat_status: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DispatchTables:
    """Catálogos auxiliares para armar una guía (motivos, modos de transporte, etc.)."""
    transfer_reasons: List[Dict[str, Any]] = field(default_factory=list)
    transport_modes: List[Dict[str, Any]] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Retention:
    id: int
    amount: float
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Perception:
    id: int
    amount: float
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Cash:
    id: int
    state: bool
    beginning_balance: float
    final_balance: Optional[float] = None
    date_opening: Optional[str] = None
    time_opening: Optional[str] = None


@dataclass
class Report:
    """Resultado de un reporte (diario o de ventas general) — payload libre."""
    data: Dict[str, Any] = field(default_factory=dict)

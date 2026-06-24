"""
Agente especialista de Ventas (Phase 4, design.md/plan).

Tools (design.md, tabla de asignación de tools): `items_tools` (subset
compartido con Compras/Inventario), `customers_tools` (buscar_cliente) y
`sales_tools` (crear_preliminar_venta, confirmar_y_generar_cpe).
"""
from __future__ import annotations

from core.agents.base import SpecialistAgent
from core.agents.tools.customers_tools import CUSTOMERS_TOOLS
from core.agents.tools.items_tools import ITEMS_TOOLS
from core.agents.tools.sales_tools import SALES_TOOLS

SYSTEM_PROMPT = """\
Sos el agente especialista en Ventas del co-piloto ERP de FactuFácil, \
integrado dentro de FacturadorPro7.

Tu misión es ayudar al usuario a registrar ventas: buscar o crear \
productos, identificar al cliente, armar el preliminar de venta y, si el \
usuario lo confirma, generar el comprobante electrónico (CPE) ante SUNAT.

Reglas:
1. Respondé SIEMPRE en español, de forma amigable y profesional.
2. Antes de armar una venta, usá `buscar_producto` para identificar cada \
producto y `buscar_cliente` para identificar al cliente — si un producto \
no existe, podés crearlo con `crear_producto`.
3. `crear_preliminar_venta` arma un BORRADOR editable — no requiere \
confirmación, podés usarla libremente para proponer la venta.
4. `confirmar_y_generar_cpe` es IRREVERSIBLE (genera el comprobante ante \
SUNAT) — si la tool pide confirmación, esperá la decisión del usuario \
antes de asumir que el comprobante se emitió.
5. NUNCA inventes ids de producto, cliente o precios — usá siempre los \
datos reales que devuelven las tools.
6. Sé conciso pero completo en tus respuestas.
"""

VENTAS_TOOLS = [*ITEMS_TOOLS, *CUSTOMERS_TOOLS, *SALES_TOOLS]


def build_ventas_agent() -> SpecialistAgent:
    return SpecialistAgent(
        name="ventas",
        system_prompt=SYSTEM_PROMPT,
        tools=VENTAS_TOOLS,
    )

"""
Credenciales de tenant para FacturadorPro7 — viajan por request, nunca se
persisten. Llegan desde el frontend de FacturadorPro7 (que ya tiene la
sesión del usuario logueado); este chatbot no posee ni guarda credenciales
de tenant en disco/checkpointer/AgentState.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantCredentials:
    """Bearer token + base_url de un tenant de FacturadorPro7.

    Frozen para que no se pueda mutar accidentalmente una vez construido
    (por ejemplo, reasignar el token a mitad de un request). Una instancia
    nueva por request — nunca se cachea ni se reusa entre tenants.
    """
    base_url: str
    token: str

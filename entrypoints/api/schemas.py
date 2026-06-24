from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje del usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión (omitir para nueva sesión)")


class SourceItem(BaseModel):
    category: str
    topic: str
    excerpt: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceItem]
    message_count: int


# ── Multi-agent ERP co-pilot schemas (additive, design.md "Data Flow" /
#    "erp-agent-api" spec) ───────────────────────────────────────────────────
#
# `tenant_base_url`/`tenant_token` are how the FacturadorPro7 frontend
# forwards its ALREADY-AUTHENTICATED session's credentials per-request
# (design.md "Credential injection" — multi-tenant credentials are
# per-request and NEVER persisted in AgentState/checkpointer/disk/logs).
# They become a `TenantCredentials` instance passed via
# `config["configurable"]["creds"]`, never a normal tool/body field that the
# LLM tool schema could see.

class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario para el co-piloto ERP.")
    session_id: str = Field(..., description="Identifica la conversación — también el thread_id del checkpointer.")
    context_module: Optional[Literal["inventario", "compras", "ventas", "logistica", "contabilidad"]] = Field(
        default=None,
        description="Módulo donde está parado el usuario en FacturadorPro7 — fast-path de ruteo sin LLM si viene seteado.",
    )
    tenant_base_url: str = Field(..., description="Base URL del tenant de FacturadorPro7 (ej. https://acme.qhipa.org.pe).")
    tenant_token: str = Field(..., description="Bearer token de la sesión YA AUTENTICADA del usuario en FacturadorPro7.")


class AgentChatResponse(BaseModel):
    session_id: str
    status: Literal["answered", "awaiting_confirmation"]
    answer: Optional[str] = None
    confirmation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Presente solo cuando status='awaiting_confirmation' — {tool_name, summary, tool_args}.",
    )


class AgentConfirmRequest(BaseModel):
    session_id: str = Field(..., description="Mismo session_id usado en /agent/chat — resume el mismo thread_id.")
    approved: bool = Field(..., description="True para ejecutar la escritura pendiente, False para cancelarla.")

"""
Entidades del dominio. Sin dependencias externas — Python puro.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


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

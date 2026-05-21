"""
Puertos (interfaces) del dominio.
El core solo habla con estas abstracciones — nunca con implementaciones concretas.
"""
from abc import ABC, abstractmethod
from typing import List

from core.domain import ChatMessage, RetrievedDocument


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

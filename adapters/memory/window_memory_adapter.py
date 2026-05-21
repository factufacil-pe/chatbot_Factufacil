"""
Adaptador de memoria — ventana deslizante en RAM.
Implementación propia sin depender de langchain.memory (removido en LangChain 1.x).
"""
from collections import deque
from typing import Dict, List

from core.domain import ChatMessage
from core.ports import MemoryPort
from infrastructure.config import Config


class WindowMemoryAdapter(MemoryPort):

    def __init__(self) -> None:
        # session_id → deque de ChatMessage con tamaño máximo k*2 (user + assistant)
        self._sessions: Dict[str, deque] = {}

    def get_history(self, session_id: str) -> List[ChatMessage]:
        if session_id not in self._sessions:
            return []
        return list(self._sessions[session_id])

    def save_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = deque(maxlen=Config.MEMORY_K * 2)
        self._sessions[session_id].append(ChatMessage(role="user", content=user_msg))
        self._sessions[session_id].append(ChatMessage(role="assistant", content=assistant_msg))

    def clear(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def get_session_info(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            return {"exists": False, "session_id": session_id}
        messages = self._sessions[session_id]
        return {
            "exists": True,
            "session_id": session_id,
            "message_count": len(messages) // 2,
            "total_messages": len(messages),
        }

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

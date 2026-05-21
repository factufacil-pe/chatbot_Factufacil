"""
Servicio principal del chatbot FactuFácil.
Orquesta LLM + RAG + memoria conversacional por sesión.
"""
import uuid
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage

from rag_system import RAGSystem
from config import Config

# ------------------------------------------------------------------ #
#  Prompt del sistema                                                  #
# ------------------------------------------------------------------ #

SYSTEM_TEMPLATE = """\
Sos el asistente virtual de {company}, un sistema de facturación electrónica peruano.

Tu misión es ayudar a los usuarios con:
- Planes y precios del sistema
- Características y funcionalidades
- Integración con SUNAT y RENIEC
- Soporte, contacto y demo

Reglas que DEBES cumplir:
1. Respondé SIEMPRE en español, de forma amigable y profesional.
2. Usá ÚNICAMENTE la información del contexto proporcionado.
3. Si no tenés suficiente información, indicá que el usuario contacte a {email} o al {phone}.
4. NUNCA inventes precios, características ni datos que no estén en el contexto.
5. Sé conciso pero completo. Usá listas cuando ayude a la claridad.

--- CONTEXTO DE {company} (fuente: base de conocimiento) ---
{context}
--- FIN DEL CONTEXTO ---

--- HISTORIAL DE CONVERSACIÓN ---
{history}
--- FIN DEL HISTORIAL ---
"""

GUARD_PHRASES = [
    "no tengo información suficiente",
    "no cuento con esa información",
    "te recomiendo contactar",
]


class ChatbotService:
    """Chatbot conversacional con RAG y memoria por sesión."""

    def __init__(self) -> None:
        print("\n=== Inicializando ChatbotService ===")
        Config.print_config()
        Config.validate()

        self.rag = RAGSystem()
        self.llm = self._build_llm()
        self._sessions: Dict[str, ConversationBufferWindowMemory] = {}
        print("✓ ChatbotService listo\n")

    # ------------------------------------------------------------------ #
    #  Construcción interna                                               #
    # ------------------------------------------------------------------ #

    def _build_llm(self) -> ChatOpenAI:
        print(f"Conectando LLM: {Config.LLM_MODEL}...")
        kwargs: dict = {
            "model": Config.LLM_MODEL,
            "api_key": Config.LLM_API_KEY,
            "temperature": Config.LLM_TEMPERATURE,
        }
        if Config.LLM_BASE_URL:
            kwargs["base_url"] = Config.LLM_BASE_URL
        return ChatOpenAI(**kwargs)

    def _get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationBufferWindowMemory(
                k=Config.MEMORY_K,
                memory_key="chat_history",
                return_messages=True,
            )
        return self._sessions[session_id]

    # ------------------------------------------------------------------ #
    #  Chat                                                               #
    # ------------------------------------------------------------------ #

    def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        """
        Procesa un mensaje y devuelve la respuesta con metadatos.

        Args:
            message:    Texto del usuario.
            session_id: ID de sesión existente o None para crear una nueva.

        Returns:
            dict con session_id, answer, sources, message_count.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        memory = self._get_memory(session_id)

        # 1. Recuperar contexto relevante
        context_docs = self.rag.retrieve(message)
        context = (
            "\n\n---\n\n".join(d.page_content for d in context_docs)
            if context_docs
            else "Sin contexto disponible."
        )

        # 2. Formatear historial de conversación
        history = self._format_history(
            memory.load_memory_variables({}).get("chat_history", [])
        )

        # 3. Construir prompt completo
        full_prompt = SYSTEM_TEMPLATE.format(
            company=Config.COMPANY_NAME,
            email=Config.COMPANY_EMAIL,
            phone=Config.COMPANY_PHONE,
            context=context,
            history=history,
        ) + f"\nUsuario: {message}\nAsistente:"

        # 4. Llamar al LLM
        response = self.llm.invoke([HumanMessage(content=full_prompt)])
        answer: str = response.content.strip()

        # 5. Guardar en memoria
        memory.save_context({"input": message}, {"output": answer})

        # 6. Armar fuentes para trazabilidad
        sources = [
            {
                "category": d.metadata.get("category", ""),
                "topic": d.metadata.get("topic", ""),
                "excerpt": d.page_content[:120] + "...",
            }
            for d in context_docs
        ]

        msg_count = len(self._sessions[session_id].chat_memory.messages) // 2

        return {
            "session_id": session_id,
            "answer": answer,
            "sources": sources,
            "message_count": msg_count,
        }

    # ------------------------------------------------------------------ #
    #  Gestión de sesiones                                                #
    # ------------------------------------------------------------------ #

    def clear_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def get_session_info(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            return {"exists": False, "session_id": session_id}
        messages = self._sessions[session_id].chat_memory.messages
        return {
            "exists": True,
            "session_id": session_id,
            "message_count": len(messages) // 2,
            "total_messages": len(messages),
        }

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _format_history(messages: list) -> str:
        if not messages:
            return "Sin historial previo."
        lines = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                lines.append(f"Usuario: {msg.content}")
            elif isinstance(msg, AIMessage):
                lines.append(f"Asistente: {msg.content}")
        return "\n".join(lines) if lines else "Sin historial previo."

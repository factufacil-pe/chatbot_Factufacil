"""
Chatbot FactuFácil — API REST con FastAPI.
Swagger UI: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from chatbot_service import ChatbotService
from config import Config


# ------------------------------------------------------------------ #
#  Startup                                                            #
# ------------------------------------------------------------------ #

chatbot: ChatbotService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chatbot
    chatbot = ChatbotService()
    yield


# ------------------------------------------------------------------ #
#  App                                                                #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="Chatbot FactuFácil",
    description=(
        "Asistente virtual inteligente para FactuFácil — "
        "Sistema de Facturación Electrónica Peruana. "
        "Usa LangChain + RAG (FAISS) + LLM (Qwen/OpenAI)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


# ------------------------------------------------------------------ #
#  Schemas                                                            #
# ------------------------------------------------------------------ #

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
    sources: list[SourceItem]
    message_count: int


# ------------------------------------------------------------------ #
#  Endpoints                                                          #
# ------------------------------------------------------------------ #

@app.get("/", tags=["info"])
def root():
    return {
        "service": "Chatbot FactuFácil",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /chat",
            "session_info": "GET /session/{session_id}",
            "clear_session": "DELETE /session/{session_id}",
            "reindex_rag": "POST /rag/reindex",
            "rag_stats": "GET /rag/stats",
            "health": "GET /health",
        },
    }


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest):
    """
    Envía un mensaje al chatbot y recibe una respuesta.

    - Si no enviás `session_id`, se crea una sesión nueva.
    - Guardá el `session_id` devuelto para mantener el contexto conversacional.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    result = chatbot.chat(message=request.message, session_id=request.session_id)
    return result


@app.get("/session/{session_id}", tags=["sessions"])
def get_session(session_id: str):
    """Devuelve información sobre una sesión activa."""
    return chatbot.get_session_info(session_id)


@app.delete("/session/{session_id}", tags=["sessions"])
def clear_session(session_id: str):
    """Elimina el historial de una sesión."""
    cleared = chatbot.clear_session(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return {"cleared": True, "session_id": session_id}


@app.post("/rag/reindex", tags=["rag"])
def reindex():
    """Reconstruye el índice FAISS desde la base de conocimiento."""
    chatbot.rag.reindex()
    return {"message": "Índice RAG reconstruido exitosamente."}


@app.get("/rag/stats", tags=["rag"])
def rag_stats():
    """Devuelve estadísticas del índice RAG."""
    return chatbot.rag.get_stats()


@app.get("/health", tags=["info"])
def health():
    return {
        "status": "ok",
        "model": Config.LLM_MODEL,
        "sessions_active": len(chatbot.list_sessions()),
    }


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
    )

from typing import List, Optional
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

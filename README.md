# Chatbot FactuFácil — LLM + RAG con LangChain

Asistente virtual inteligente para **FactuFácil** (https://factufacil.pe),  
sistema de facturación electrónica peruano.

---

## Arquitectura

```
Usuario → FastAPI (main.py)
              │
              ▼
        ChatbotService (chatbot_service.py)
         ├── RAGSystem (rag_system.py)
         │    ├── FAISS vector store  ← índice local
         │    └── HuggingFace Embeddings (paraphrase-multilingual-MiniLM-L12-v2)
         ├── ConversationBufferWindowMemory (k=8 turnos)
         └── LLM — Qwen3 via Alibaba DashScope (o OpenAI)
              └── Prompt = sistema + contexto RAG + historial + pregunta
```

**Flujo por mensaje:**

1. El mensaje del usuario llega a `POST /chat`.
2. `RAGSystem.retrieve()` busca los 4 chunks más relevantes en FAISS.
3. El contexto recuperado + historial de sesión se inyectan en el prompt.
4. El LLM genera una respuesta fundamentada en el contexto.
5. La respuesta y fuentes se devuelven como JSON.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| API | FastAPI + Uvicorn |
| Orquestación | LangChain >= 0.2 |
| Vector store | FAISS (local, sin servidor) |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| LLM | Qwen3 via Alibaba DashScope (OpenAI-compatible) o GPT |
| Memoria | `ConversationBufferWindowMemory` (k=8) |

---

## Instalación

```bash
# 1. Clonar / entrar al directorio
cd proyecto_final_factufacil

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# → Editá .env y agregá tu ALIBABA_API_KEY (o OPENAI_API_KEY)
```

---

## Ejecución

```bash
# Iniciar el servidor (el índice FAISS se crea automáticamente la primera vez)
python main.py

# O con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Swagger UI:** http://localhost:8000/docs

---

## Uso de la API

### Nuevo chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cuánto cuesta el plan PRO?"}'
```

### Continuar conversación (mantener contexto)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Y qué diferencia tiene con el Básico?", "session_id": "TU_SESSION_ID"}'
```

### Respuesta de ejemplo

```json
{
  "session_id": "abc-123",
  "answer": "El plan PRO cuesta S/.95 al mes (S/.950 al año)...",
  "sources": [
    {
      "category": "precios",
      "topic": "planes",
      "excerpt": "Plan PRO — S/.95 por mes..."
    }
  ],
  "message_count": 1
}
```

---

## Tests

```bash
# Con el servidor corriendo:
python test_chatbot.py
```

---

## Otros endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `GET` | `/rag/stats` | Info del índice FAISS |
| `POST` | `/rag/reindex` | Reconstruir índice RAG |
| `GET` | `/session/{id}` | Info de una sesión |
| `DELETE` | `/session/{id}` | Limpiar historial de sesión |

---

## Manejo de alucinaciones

- El prompt instruye al LLM a usar **solo** el contexto recuperado.
- Si el contexto no contiene la respuesta, el modelo indica contactar a ventas@factufacil.pe.
- Las fuentes usadas se devuelven en cada respuesta para trazabilidad.

---

## Estructura del proyecto

```
proyecto_final_factufacil/
├── main.py              # API FastAPI
├── chatbot_service.py   # Orquestación LLM + RAG + memoria
├── rag_system.py        # FAISS + embeddings
├── knowledge_base.py    # Datos de FactuFácil
├── config.py            # Configuración centralizada
├── test_chatbot.py      # Tests funcionales
├── requirements.txt
├── .env.example
└── data/
    └── faiss_index/     # Generado automáticamente al iniciar
```

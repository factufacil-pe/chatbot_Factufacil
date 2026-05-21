FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias primero (capa cacheada)
COPY requirements.txt .
# CPU-only torch to avoid 2GB CUDA variant pulled by sentence-transformers
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# El índice FAISS se genera en runtime en /app/data/faiss_index
# (se monta como volumen en docker-compose para persistencia)

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "entrypoints.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

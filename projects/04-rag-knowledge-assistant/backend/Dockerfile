# Backend image for Fly.io / Render.
FROM python:3.11-slim

WORKDIR /app

# Install deps first for better layer caching.
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && pip install --no-cache-dir "uvicorn[standard]"

COPY app ./app

ENV RAG_DB_PATH=/data/rag.db
ENV LLM_PROVIDER=ollama
ENV EMBED_PROVIDER=ollama
EXPOSE 8000

# /data is mounted as a persistent volume in fly.toml.
CMD ["sh", "-c", "mkdir -p /data && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

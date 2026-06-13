"""FastAPI application exposing the RAG knowledge assistant."""

from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import __version__
from .config import get_settings
from .embeddings import build_embeddings
from .llm import build_chat
from .rag import RAGService
from .store import VectorStore

settings = get_settings()
app = FastAPI(title="RAG Knowledge Assistant", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_origins == "*" else settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

store = VectorStore(settings.db_path)
service = RAGService(store, build_embeddings(settings), build_chat(settings), settings)


class IngestText(BaseModel):
    source: str
    text: str


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "llm_provider": type(service.chat).__name__,
        "embed_provider": type(service.embeddings).__name__,
    }


@app.get("/documents")
def documents() -> dict:
    return {"documents": store.list_documents()}


@app.post("/ingest")
def ingest(payload: IngestText) -> dict:
    try:
        return service.ingest(payload.source, payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), source: str = Form("")) -> dict:
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="Only UTF-8 text/markdown files are supported."
        ) from exc
    try:
        return service.ingest(source or file.filename or "uploaded", text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Stream the answer as NDJSON: a citations frame, then token frames, then done."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    citations, token_stream = service.answer_stream(req.question)

    def event_stream() -> Iterator[str]:
        yield json.dumps({"type": "citations", "citations": [c.__dict__ for c in citations]}) + "\n"
        for token in token_stream:
            yield json.dumps({"type": "token", "value": token}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

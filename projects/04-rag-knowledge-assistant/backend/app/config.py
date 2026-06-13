"""Application configuration, sourced from environment variables.

Defaults are chosen so a fresh clone runs with zero external services:
when ``LLM_PROVIDER``/``EMBED_PROVIDER`` are left as ``ollama`` but no Ollama
host is reachable, the providers fall back gracefully (see ``llm.py`` /
``embeddings.py``). Set them to ``fake`` to force the offline implementations
(used by the test suite and CI).

Each field reads its environment variable via a ``default_factory`` so the value
is resolved at *instantiation* time, not at import time — this keeps the config
honest under reloads/overrides and makes it trivially testable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(key: str, default: str):
    return field(default_factory=lambda: os.getenv(key, default))


def _env_int(key: str, default: int):
    return field(default_factory=lambda: int(os.getenv(key, str(default))))


@dataclass
class Settings:
    # Storage
    db_path: str = _env("RAG_DB_PATH", "rag.db")

    # Chunking
    chunk_size: int = _env_int("RAG_CHUNK_SIZE", 800)
    chunk_overlap: int = _env_int("RAG_CHUNK_OVERLAP", 120)

    # Retrieval
    top_k: int = _env_int("RAG_TOP_K", 4)

    # Providers: "ollama" or "fake"
    llm_provider: str = _env("LLM_PROVIDER", "ollama")
    embed_provider: str = _env("EMBED_PROVIDER", "ollama")

    # Ollama
    ollama_host: str = _env("OLLAMA_HOST", "http://localhost:11434")
    ollama_chat_model: str = _env("OLLAMA_CHAT_MODEL", "llama3.2")
    ollama_embed_model: str = _env("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # CORS (comma-separated origins; "*" allows all)
    cors_origins: str = _env("RAG_CORS_ORIGINS", "*")


def get_settings() -> Settings:
    return Settings()

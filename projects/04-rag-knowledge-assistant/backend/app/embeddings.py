"""Pluggable text-embedding providers.

``OllamaEmbeddings`` calls a local/remote Ollama server. ``FakeEmbeddings`` is a
deterministic, dependency-free hashing embedder used for tests, CI, and as a
graceful fallback when Ollama is unreachable. Both return L2-normalized vectors
so the store can use a plain dot product as cosine similarity.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol

import httpx

from .config import Settings


class EmbeddingProvider(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


class FakeEmbeddings:
    """Deterministic hashing embedder — no network, stable across runs.

    Tokens are hashed into a fixed-size bag-of-words vector. It won't rival a
    real model, but it gives meaningful, reproducible nearest-neighbor results
    for testing the retrieval pipeline offline.
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for token in text.lower().split():
                h = int(hashlib.md5(token.encode()).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            out.append(_normalize(vec))
        return out


class OllamaEmbeddings:
    """Embeddings via Ollama's ``/api/embeddings`` endpoint."""

    def __init__(self, host: str, model: str, dim: int = 768) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        with httpx.Client(timeout=60.0) as client:
            for text in texts:
                resp = client.post(
                    f"{self.host}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                vec = resp.json()["embedding"]
                self.dim = len(vec)
                out.append(_normalize(vec))
        return out


def build_embeddings(settings: Settings) -> EmbeddingProvider:
    """Select an embedding provider, falling back to FakeEmbeddings offline."""
    if settings.embed_provider == "fake":
        return FakeEmbeddings()

    provider = OllamaEmbeddings(settings.ollama_host, settings.ollama_embed_model)
    try:
        httpx.get(f"{provider.host}/api/tags", timeout=2.0).raise_for_status()
        return provider
    except Exception:  # noqa: BLE001 - any connection issue means fall back
        return FakeEmbeddings()

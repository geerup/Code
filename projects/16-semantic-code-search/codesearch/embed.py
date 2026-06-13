"""Embedding backends.

Search depends only on the ``Embedder`` protocol. ``HashingEmbedder`` is a
deterministic, dependency-free TF-style embedder (feature hashing) so indexing,
ranking, and tests run fully offline. ``OllamaEmbedder`` swaps in real neural
embeddings for production quality.
"""
from __future__ import annotations

import json
import math
import re
import urllib.request
from typing import Protocol

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def tokenize(text: str) -> list[str]:
    """Split identifiers into subwords so `getUserName` ~ `user name`."""
    out: list[str] = []
    for tok in _TOKEN.findall(text):
        parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", tok).replace("_", " ").split()
        out.extend(p.lower() for p in parts)
    return out


class Embedder(Protocol):
    dim: int

    def embed(self, text: str) -> list[float]:  # pragma: no cover - protocol
        ...


class HashingEmbedder:
    """Feature-hashing bag-of-words with L2 normalization. Offline + deterministic."""

    def __init__(self, dim: int = 512):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in tokenize(text):
            h = hash_token(tok)
            sign = 1.0 if (h >> 31) & 1 else -1.0
            vec[h % self.dim] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


def hash_token(tok: str) -> int:
    """Stable FNV-1a hash (independent of PYTHONHASHSEED)."""
    h = 2166136261
    for ch in tok.encode():
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434", dim: int = 768):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        req = urllib.request.Request(
            f"{self.base_url}/api/embeddings",
            data=json.dumps({"model": self.model, "prompt": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            return json.loads(resp.read())["embedding"]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0

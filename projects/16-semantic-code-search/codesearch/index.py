"""Chunk source files, embed the chunks, and rank them against a query."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .embed import Embedder, cosine

CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".rb", ".md"}


@dataclass
class Chunk:
    path: str
    start_line: int
    end_line: int
    text: str


@dataclass
class Hit:
    path: str
    start_line: int
    end_line: int
    score: float
    preview: str


def chunk_text(text: str, path: str, window: int = 30, stride: int = 20) -> list[Chunk]:
    """Sliding window over lines so a match maps to a line range."""
    lines = text.splitlines()
    chunks: list[Chunk] = []
    if not lines:
        return chunks
    i = 0
    while i < len(lines):
        block = lines[i : i + window]
        chunks.append(Chunk(path, i + 1, i + len(block), "\n".join(block)))
        if i + window >= len(lines):
            break
        i += stride
    return chunks


def iter_code_files(root: str | Path):
    root = Path(root)
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in CODE_EXTS and ".git" not in p.parts and "node_modules" not in p.parts:
            yield p


class Index:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.chunks: list[Chunk] = []
        self.vectors: list[list[float]] = []

    def add_text(self, text: str, path: str) -> int:
        added = 0
        for ch in chunk_text(text, path):
            self.chunks.append(ch)
            self.vectors.append(self.embedder.embed(ch.text))
            added += 1
        return added

    def build(self, root: str | Path) -> int:
        for p in iter_code_files(root):
            try:
                self.add_text(p.read_text(errors="ignore"), str(p))
            except OSError:
                continue
        return len(self.chunks)

    def search(self, query: str, k: int = 5) -> list[Hit]:
        q = self.embedder.embed(query)
        scored = sorted(
            ((cosine(q, v), ch) for v, ch in zip(self.vectors, self.chunks)),
            key=lambda t: t[0],
            reverse=True,
        )
        hits: list[Hit] = []
        for sc, ch in scored[:k]:
            preview = "\n".join(ch.text.splitlines()[:3])
            hits.append(Hit(ch.path, ch.start_line, ch.end_line, round(sc, 4), preview))
        return hits

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({
            "dim": self.embedder.dim,
            "chunks": [asdict(c) for c in self.chunks],
            "vectors": self.vectors,
        }))

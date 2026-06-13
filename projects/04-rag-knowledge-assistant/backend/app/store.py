"""SQLite-backed vector store with brute-force cosine search.

Embeddings are stored L2-normalized, so cosine similarity is a dot product.
Brute force is more than adequate for a portfolio-scale corpus and keeps the
dependency surface tiny (stdlib sqlite3 + numpy). Swapping in a real ANN index
is exactly what portfolio project #8 explores.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

import numpy as np


@dataclass
class SearchHit:
    chunk_id: int
    document_id: int
    source: str
    text: str
    score: float


class VectorStore:
    def __init__(self, db_path: str = "rag.db") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def add_document(self, source: str, chunks: list[str], embeddings: list[list[float]]) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must be the same length")
        cur = self.conn.execute("INSERT INTO documents (source) VALUES (?)", (source,))
        document_id = int(cur.lastrowid)
        self.conn.executemany(
            "INSERT INTO chunks (document_id, text, embedding) VALUES (?, ?, ?)",
            [(document_id, c, json.dumps(e)) for c, e in zip(chunks, embeddings, strict=True)],
        )
        self.conn.commit()
        return document_id

    def search(self, query_embedding: list[float], top_k: int = 4) -> list[SearchHit]:
        rows = self.conn.execute(
            """
            SELECT c.id, c.document_id, c.text, c.embedding, d.source
            FROM chunks c JOIN documents d ON d.id = c.document_id
            """
        ).fetchall()
        if not rows:
            return []

        matrix = np.array([json.loads(r["embedding"]) for r in rows], dtype=np.float32)
        query = np.array(query_embedding, dtype=np.float32)
        # Vectors are pre-normalized, so dot product == cosine similarity.
        scores = matrix @ query
        order = np.argsort(-scores)[:top_k]
        return [
            SearchHit(
                chunk_id=int(rows[i]["id"]),
                document_id=int(rows[i]["document_id"]),
                source=rows[i]["source"],
                text=rows[i]["text"],
                score=float(scores[i]),
            )
            for i in order
        ]

    def list_documents(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT d.id, d.source, d.created_at, COUNT(c.id) AS chunk_count
            FROM documents d LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id ORDER BY d.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()

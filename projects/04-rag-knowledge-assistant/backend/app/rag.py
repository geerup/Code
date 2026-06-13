"""Retrieval-augmented generation: tie ingestion, retrieval and the LLM together."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .chunking import chunk_text
from .config import Settings
from .embeddings import EmbeddingProvider
from .llm import ChatProvider
from .store import SearchHit, VectorStore

SYSTEM_PROMPT = (
    "You are a precise knowledge assistant. Answer the user's question using ONLY "
    "the provided context. Cite sources inline with bracketed numbers like [1] that "
    "refer to the numbered context passages. If the context does not contain the "
    "answer, say so plainly rather than guessing."
)


@dataclass
class Citation:
    index: int
    source: str
    score: float
    snippet: str


def build_prompt(question: str, hits: list[SearchHit]) -> str:
    """Assemble the user prompt with numbered, citable context passages."""
    if not hits:
        return f"Context:\n(none)\n\nQuestion: {question}"
    blocks = []
    for i, hit in enumerate(hits, start=1):
        blocks.append(f"[{i}] (source: {hit.source})\n{hit.text}")
    context = "\n\n".join(blocks)
    return f"Context:\n{context}\n\nQuestion: {question}"


class RAGService:
    def __init__(
        self,
        store: VectorStore,
        embeddings: EmbeddingProvider,
        chat: ChatProvider,
        settings: Settings,
    ) -> None:
        self.store = store
        self.embeddings = embeddings
        self.chat = chat
        self.settings = settings

    def ingest(self, source: str, text: str) -> dict:
        chunks = chunk_text(text, self.settings.chunk_size, self.settings.chunk_overlap)
        if not chunks:
            raise ValueError("document produced no chunks (is it empty?)")
        vectors = self.embeddings.embed(chunks)
        document_id = self.store.add_document(source, chunks, vectors)
        return {"document_id": document_id, "chunks": len(chunks), "source": source}

    def retrieve(self, question: str) -> list[SearchHit]:
        query_vec = self.embeddings.embed([question])[0]
        return self.store.search(query_vec, self.settings.top_k)

    def answer_stream(self, question: str) -> tuple[list[Citation], Iterator[str]]:
        hits = self.retrieve(question)
        citations = [
            Citation(
                index=i,
                source=h.source,
                score=round(h.score, 4),
                snippet=h.text[:200],
            )
            for i, h in enumerate(hits, start=1)
        ]
        prompt = build_prompt(question, hits)
        return citations, self.chat.stream(SYSTEM_PROMPT, prompt)

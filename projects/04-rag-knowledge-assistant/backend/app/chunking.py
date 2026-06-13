"""Split documents into overlapping, word-aware chunks for embedding.

The splitter packs whole words up to ``chunk_size`` characters, then starts the
next chunk ``overlap`` characters back so context isn't lost across boundaries.
"""

from __future__ import annotations

import re


def normalize(text: str) -> str:
    """Collapse runs of whitespace while preserving paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ newlines to a double newline, and spaces/tabs to single space.
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Return a list of overlapping chunks.

    Splitting happens on word boundaries so we never cut a word in half. The
    ``overlap`` is approximate (measured in characters) and is clamped to be
    smaller than ``chunk_size`` to guarantee forward progress.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    overlap = max(0, min(overlap, chunk_size - 1))

    text = normalize(text)
    if not text:
        return []

    words = text.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        # +1 accounts for the joining space.
        added = len(word) + (1 if current else 0)
        if current and current_len + added > chunk_size:
            chunks.append(" ".join(current))
            # Build the overlap tail from the end of the current chunk.
            tail: list[str] = []
            tail_len = 0
            for w in reversed(current):
                wlen = len(w) + (1 if tail else 0)
                if tail_len + wlen > overlap:
                    break
                tail.insert(0, w)
                tail_len += wlen
            current = tail
            current_len = tail_len

        current.append(word)
        current_len += added

    if current:
        chunks.append(" ".join(current))

    return chunks

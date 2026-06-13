"""Pluggable chat-completion providers with streaming support.

``OllamaChat`` streams tokens from a local/remote Ollama server.
``FakeChat`` is an offline, deterministic stand-in that echoes a grounded answer
built from the retrieved context, so the full RAG flow works without a model.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

import httpx

from .config import Settings


class ChatProvider(Protocol):
    def stream(self, system: str, prompt: str) -> Iterator[str]: ...


class FakeChat:
    """Offline provider: returns a short, deterministic, context-grounded reply."""

    def stream(self, system: str, prompt: str) -> Iterator[str]:
        # The prompt embeds the question after a "Question:" marker (see rag.py).
        question = prompt.split("Question:")[-1].split("\n")[0].strip()
        has_context = "Context:" in prompt and "[1]" in prompt
        if has_context:
            answer = (
                f"Based on the retrieved sources, here is a grounded answer to "
                f'"{question}". See the cited passages [1] for details.'
            )
        else:
            answer = (
                "I don't have any relevant information in the knowledge base to "
                "answer that yet. Try ingesting a document first."
            )
        for word in answer.split(" "):
            yield word + " "


class OllamaChat:
    """Streaming chat via Ollama's ``/api/chat`` endpoint."""

    def __init__(self, host: str, model: str) -> None:
        self.host = host.rstrip("/")
        self.model = model

    def stream(self, system: str, prompt: str) -> Iterator[str]:
        import json

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
        }
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", f"{self.host}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token


def build_chat(settings: Settings) -> ChatProvider:
    """Select a chat provider, falling back to FakeChat offline."""
    if settings.llm_provider == "fake":
        return FakeChat()

    provider = OllamaChat(settings.ollama_host, settings.ollama_chat_model)
    try:
        httpx.get(f"{provider.host}/api/tags", timeout=2.0).raise_for_status()
        return provider
    except Exception:  # noqa: BLE001 - any connection issue means fall back
        return FakeChat()

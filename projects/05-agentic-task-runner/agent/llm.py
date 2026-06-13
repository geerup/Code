"""LLM client abstraction.

The agent depends on the small ``LLM`` protocol, never on a concrete provider,
so it runs against a local Ollama model in production and a scripted fake in
tests — no network required.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Protocol


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str:  # pragma: no cover - protocol
        ...


class OllamaLLM:
    """Talks to a local Ollama server (https://ollama.com)."""

    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (local URL)
            data = json.loads(resp.read())
        return data["message"]["content"]


class ScriptedLLM:
    """Deterministic LLM for tests/demos: returns queued replies in order."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if not self._replies:
            return "FINAL: (no more scripted replies)"
        return self._replies.pop(0)

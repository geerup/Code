"""LLM clients. The bot takes a message list so multi-turn memory is native."""
from __future__ import annotations

import json
import urllib.request
from typing import Protocol


class LLM(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str:  # pragma: no cover
        ...


class OllamaLLM:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list[dict[str, str]]) -> str:
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"model": self.model, "messages": messages, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            return json.loads(resp.read())["message"]["content"]


class EchoLLM:
    """Deterministic test LLM: echoes the last user message, prefixed."""

    def __init__(self, prefix: str = "echo: "):
        self.prefix = prefix
        self.seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.seen.append(messages)
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return self.prefix + last_user

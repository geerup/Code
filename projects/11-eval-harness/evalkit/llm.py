"""Concrete LLM clients for the harness (Ollama + a scripted fake)."""
from __future__ import annotations

import json
import urllib.request


class OllamaLLM:
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
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            return json.loads(resp.read())["message"]["content"]


class ScriptedLLM:
    """Maps prompt -> reply for deterministic evals; falls back to echo."""

    def __init__(self, table: dict[str, str] | None = None, default: str = ""):
        self.table = table or {}
        self.default = default

    def complete(self, system: str, user: str) -> str:
        return self.table.get(user, self.default or user)

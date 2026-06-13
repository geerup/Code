"""LLM clients for the Game Master."""
from __future__ import annotations

import json
import urllib.request


class OllamaLLM:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, system: str, user: str) -> str:
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"model": self.model, "stream": False, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            return json.loads(r.read())["message"]["content"]


class ScriptedLLM:
    """Returns queued replies (for tests/demos)."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)

    def complete(self, system: str, user: str) -> str:
        return self._replies.pop(0) if self._replies else '{"narration":"Nothing happens.","effects":[]}'

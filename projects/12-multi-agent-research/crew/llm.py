"""LLM + tool abstractions shared by the crew. Mockable for offline tests."""
from __future__ import annotations

import json
import urllib.request
from typing import Callable, Protocol


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        ...


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
        with urllib.request.urlopen(req, timeout=180) as r:  # noqa: S310
            return json.loads(r.read())["message"]["content"]


class ScriptedLLM:
    """Returns replies based on a role tag found in the system prompt, so each
    agent can be given distinct canned output in tests."""

    def __init__(self, by_role: dict[str, list[str]] | None = None, default: str = "(no reply)"):
        self.by_role = {k: list(v) for k, v in (by_role or {}).items()}
        self.default = default
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        for role, replies in self.by_role.items():
            if role in system and replies:
                return replies.pop(0)
        return self.default


# A SearchTool returns a list of (title, snippet) results for a query.
SearchTool = Callable[[str], list[tuple[str, str]]]


def static_search(corpus: dict[str, str]) -> SearchTool:
    """A deterministic offline 'search' over an in-memory corpus (keyword match)."""
    def search(query: str) -> list[tuple[str, str]]:
        q = set(query.lower().split())
        scored = []
        for title, text in corpus.items():
            overlap = len(q & set(text.lower().split()))
            if overlap:
                scored.append((overlap, title, text[:200]))
        scored.sort(reverse=True)
        return [(t, s) for _, t, s in scored[:3]]
    return search

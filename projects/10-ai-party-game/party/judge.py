"""The AI judge ranks answers to a prompt. Backed by an LLM in production and a
deterministic stub in tests. The judge returns an ordered list of player names,
best first."""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Protocol


class Judge(Protocol):
    def rank(self, prompt: str, answers: list[tuple[str, str]]) -> list[str]:  # pragma: no cover
        ...


JUDGE_SYSTEM = """You are the witty host of a party game. Given a PROMPT and several
players' ANSWERS, rank them funniest-first. Reply ONLY as JSON:
{"ranking": ["<player name>", ...]} using the exact player names provided."""


class LLMJudge:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def rank(self, prompt: str, answers: list[tuple[str, str]]) -> list[str]:
        listing = "\n".join(f"- {name}: {ans}" for name, ans in answers)
        user = f"PROMPT: {prompt}\nANSWERS:\n{listing}"
        raw = self._complete(JUDGE_SYSTEM, user)
        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            ranking = json.loads(m.group(0))["ranking"]
            return [str(n) for n in ranking]
        except Exception:
            return [name for name, _ in answers]  # fall back to submission order

    def _complete(self, system: str, user: str) -> str:
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


class ScriptedJudge:
    """Returns a preset ranking (names) for tests."""

    def __init__(self, ranking: list[str]):
        self.ranking = ranking

    def rank(self, prompt: str, answers: list[tuple[str, str]]) -> list[str]:
        return list(self.ranking)

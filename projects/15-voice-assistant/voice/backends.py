"""Concrete backends. Real ones target local/HTTP services; fakes drive tests.

Production wiring (commented in the README): Whisper for STT, Ollama for the LLM,
and Piper/Coqui for TTS — all runnable locally so the assistant is private/free.
"""
from __future__ import annotations

import json
import urllib.request


class OllamaLLM:
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list[dict]) -> str:
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"model": self.model, "messages": messages, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            return json.loads(r.read())["message"]["content"]


# --- fakes for tests / offline demo ------------------------------------------

class FakeSTT:
    """Maps audio bytes to a transcript via a lookup, else decodes utf-8."""

    def __init__(self, table: dict[bytes, str] | None = None):
        self.table = table or {}

    def transcribe(self, audio: bytes) -> str:
        if audio in self.table:
            return self.table[audio]
        try:
            return audio.decode("utf-8")
        except UnicodeDecodeError:
            return ""


class EchoLLM:
    def chat(self, messages: list[dict]) -> str:
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"You said: {last}"


class FakeTTS:
    """'Synthesizes' by returning a deterministic byte blob derived from text."""

    def synthesize(self, text: str) -> bytes:
        return b"WAV:" + text.encode("utf-8")

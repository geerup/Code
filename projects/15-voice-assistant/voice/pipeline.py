"""Voice assistant pipeline: speech -> text -> LLM -> text -> speech.

Each stage (STT, LLM, TTS) is an injected component behind a small Protocol, so
the orchestration — turn handling, conversation memory, barge-in/cancellation,
and latency accounting — is unit-tested with fakes and no audio hardware.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol


class STT(Protocol):
    def transcribe(self, audio: bytes) -> str:  # pragma: no cover
        ...


class LLM(Protocol):
    def chat(self, messages: list[dict]) -> str:  # pragma: no cover
        ...


class TTS(Protocol):
    def synthesize(self, text: str) -> bytes:  # pragma: no cover
        ...


@dataclass
class TurnResult:
    transcript: str
    reply: str
    audio: bytes
    cancelled: bool = False
    timings_ms: dict = field(default_factory=dict)


class VoiceAssistant:
    def __init__(self, stt: STT, llm: LLM, tts: TTS, system: str = "You are a helpful voice assistant. Keep replies short.", max_turns: int = 10):
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.system = system
        self.max_turns = max_turns
        self.history: list[dict] = []
        self._clock = time.perf_counter

    def set_clock(self, fn) -> None:  # for deterministic timing tests
        self._clock = fn

    def _messages(self) -> list[dict]:
        return [{"role": "system", "content": self.system}, *self.history]

    def handle_turn(self, audio: bytes, is_cancelled=None) -> TurnResult:
        """Run one full voice turn. `is_cancelled()` lets a caller barge in;
        if it returns True before TTS, we abandon the turn (no audio out)."""
        timings: dict[str, float] = {}

        t0 = self._clock()
        transcript = self.stt.transcribe(audio).strip()
        timings["stt"] = self._ms(t0)

        if not transcript:
            return TurnResult("", "", b"", timings_ms=timings)

        self.history.append({"role": "user", "content": transcript})
        self._trim()

        t1 = self._clock()
        reply = self.llm.chat(self._messages())
        timings["llm"] = self._ms(t1)
        self.history.append({"role": "assistant", "content": reply})
        self._trim()

        # Barge-in: skip speaking if the user interrupted.
        if is_cancelled and is_cancelled():
            return TurnResult(transcript, reply, b"", cancelled=True, timings_ms=timings)

        t2 = self._clock()
        audio_out = self.tts.synthesize(reply)
        timings["tts"] = self._ms(t2)
        timings["total"] = timings.get("stt", 0) + timings.get("llm", 0) + timings.get("tts", 0)
        return TurnResult(transcript, reply, audio_out, timings_ms=timings)

    def _trim(self) -> None:
        # Keep the last max_turns messages (user+assistant) for context bounds.
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def _ms(self, start: float) -> float:
        return round((self._clock() - start) * 1000, 2)

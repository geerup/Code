# 🎙️ Voice AI Assistant (#15)

A voice assistant pipeline — **speech → text → LLM → text → speech** — built so
the hard parts (turn handling, conversation memory, **barge-in/cancellation**,
and **latency accounting** per stage) are real and **unit-tested**, while the
STT/LLM/TTS backends are pluggable.

## Architecture
Each stage is an injected component behind a `Protocol`:
- **STT** → Whisper (local) in production, `FakeSTT` in tests.
- **LLM** → `OllamaLLM` in production, `EchoLLM` in tests.
- **TTS** → Piper/Coqui (local) in production, `FakeTTS` in tests.

The orchestrator (`voice/pipeline.py`) owns the parts that actually need
testing:
- **Memory** with a turn cap (bounded context).
- **Barge-in:** if `is_cancelled()` fires before TTS, the turn is abandoned —
  no talking over the user.
- **Latency breakdown:** per-stage timings (clock is injectable, so timing is
  tested deterministically) — essential for a responsive voice UX.

## Run
```bash
python -m unittest discover -s tests     # full pipeline, no audio hardware
```
Production wiring (Whisper + Ollama + Piper, all local/free) is described above;
the orchestration code doesn't change.

## What I learned / next
- Composing a multi-stage realtime pipeline, why barge-in and per-stage latency
  matter for voice, and testing time without sleeping.
- Next: streaming partial transcripts + token-by-token TTS to cut perceived
  latency, and VAD-based endpointing.

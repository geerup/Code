# 🎉 Multiplayer AI Party Game (#10) ★

A "Quiplash"-style party game where an **AI hosts and judges**: each round a
prompt is posed, every player submits one answer, and an LLM judge ranks them
funniest-first to award points. Create a room, share the 4-letter code, and play
across devices.

## Design
- **Authoritative room state machine** (`party/room.py`): `LOBBY → ANSWERING →
  REVEAL`, with join rules, one-answer-per-player enforcement, and points by
  rank. The room is the single source of truth; the network layer only reads/
  writes it.
- **Injectable AI judge** (`party/judge.py`): `LLMJudge` (Ollama) in production,
  `ScriptedJudge` in tests. The judge returns an ordered list of names; the room
  **defensively re-ranks anyone the model omits**, so a sloppy LLM response can't
  drop a player.
- **Stdlib server** with poll-based sync (no deps) → deploys anywhere.

## Tested (`tests/test_party.py`, 10 tests)
lobby/join rules · can't start with <2 players · no joining mid-game ·
one-answer enforcement · empty-answer rejection · **points awarded by rank** ·
**scores accumulate across rounds** · **judge omitting a name still ranks everyone**.

## Run
```bash
python -m unittest discover -s tests     # full game logic, offline
python server.py                         # http://localhost:8080 (open several tabs)
```

## What I learned / next
- Modeling multiplayer rounds as an authoritative state machine, and hardening
  against unreliable LLM output in a scoring path.
- Next: WebSocket push instead of polling, answer-shuffled voting (players vote,
  not just the AI), and reconnection by player id.

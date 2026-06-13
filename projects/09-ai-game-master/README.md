# 🐉 AI Game Master (#09) ★

A text-adventure **Game Master** powered by an LLM — but with the one design
decision that makes LLM games actually work: **the engine owns the authoritative
state, the model only narrates and *proposes* changes.**

## How a turn works
1. The engine sends the model the **current world state** (location, exits,
   items, inventory, flags) + the player's action.
2. The model replies with JSON: `{"narration": ..., "effects": [...]}`.
3. The engine **validates and applies** each effect against real game rules
   (`World.apply_all`). A hallucinated `move` to a non-adjacent room or a `take`
   of an item that isn't there is **rejected** — the model can't talk the game
   into an impossible state.

This "LLM proposes, engine disposes" pattern is the heart of robust AI games
(and mirrors the validate-then-trust idea in #07).

## Run
```bash
python -m unittest discover -s tests     # world rules + GM turn handling (offline)
python server.py                         # http://localhost:8080 — play in the browser
```

## Tests highlight
- Valid effects apply; **hallucinated effects are rejected** while the rest of a
  turn still applies; fenced/plain-text model replies are both handled.

## What I learned / next
- Keeping authoritative state out of the LLM, structured effect protocols, and
  validating generated actions against game rules.
- Next: persistent multi-session saves (reuse #24), richer rule systems
  (combat, NPCs via #14), and streaming narration.

# 🌉 AI + Games Bridge — "describe → playable" (#07)

Type a level idea in plain English; get a **validated, guaranteed-playable JSON
level** a game can load (compatible with the Level Editor #21 / arcade #19 tile
format). The interesting engineering isn't the prompt — it's making an LLM's
output **trustworthy enough to feed an engine**.

## The reliability pipeline
1. **Prompt** the model for strict JSON (`generate.py`).
2. **Parse** tolerantly — strip code fences / surrounding prose.
3. **Validate** against a schema *and* a playability check: exactly one spawn &
   goal, valid tile ids, correct length, and a **BFS proving the goal is
   reachable** from spawn (`schema.py`).
4. **Repair** on failure: deterministically rebuild a bordered, reachable level
   (carrying over the model's coins/hazards where they fit) so the bridge
   **never returns a broken level**.

This validate-then-repair pattern is the general trick for wiring generative
models to systems that can't tolerate malformed input.

## Run
```bash
python cli.py "a cramped dungeon with hazards near the goal" --json   # needs Ollama
python -m unittest discover -s tests                                   # offline
```

## What I learned / next
- Treating LLM output as untrusted input: schema validation, semantic checks
  (reachability), and graceful repair.
- Next: constrained decoding / JSON-schema-guided generation, difficulty
  scoring, and round-tripping edits back into a prompt.

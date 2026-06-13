# 🗣️ AI NPC Dialogue Engine (#14)

A reusable dialogue system for games: a **branching dialogue graph** with
choices gated by conditions over a shared variable store (trust, gold, quest
flags…), plus an optional **LLM free-talk** mode for open-ended, in-character
replies. Pure and DOM-free, so it's unit-tested and embeddable anywhere — it
feeds the AI Game Master (#09).

## Two layers
- **Scripted graph** (`DialogueEngine`): deterministic branching, condition-gated
  choices (`requires`), and side effects (`set`) that mutate game state. Great
  for authored, testable conversations.
- **LLM free-talk** (`buildPersonaPrompt` + `freeTalk`): grounds an injected LLM
  in the NPC's persona, facts, and current state for dynamic replies. The model
  is mocked in tests.

## Run
```bash
npm test          # engine + persona tests (node --test)
npm run serve     # http://localhost:8085 — a guard you can bribe
```

## Graph shape
```js
{ start: 'greet', nodes: { greet: { text, choices: [
  { label, to, requires: { var, op, value }, set: { var: value } }
] } } }
```

## What I learned / next
- Modeling dialogue as a condition-gated state machine; grounding an LLM in
  structured state to keep it in character.
- Next: hybrid mode (LLM proposes choices constrained to the graph), voice via
  #15, and a visual graph editor.

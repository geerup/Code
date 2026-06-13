# 🐦 One Button Ascent (#23) — Game Jam

A tiny game built to a constraint — the jam theme **ONE BUTTON**. Hold to flap
upward, release to fall, thread the gaps in scrolling walls. The point of this
project is **shipping something complete under tight scope**: one mechanic, one
input, one screen — fully playable and tested.

## Scope discipline
- **One mechanic, done well.** Gravity + a single thrust input. No menus, no
  upgrades — just the core loop.
- **Deterministic obstacle stream** (seeded PRNG) → fair runs and a testable
  simulation.
- **Engine/render split** (`src/game.js` is rules only) so the loop is
  unit-tested.

## Run
```bash
npm test          # rules engine (node --test)
npm run serve     # http://localhost:8087 — Space / mouse / touch
```

## What I learned / next
- Ruthless scoping, designing around a constraint, and shipping a finished small
  thing instead of an unfinished big one.
- Next: difficulty ramp over time, a daily-seed leaderboard (wire to #22), and
  juice (screen shake, particles).

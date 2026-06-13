# 🐍 Gravity Snake (#19)

A retro Snake clone with a twist: **every apple you eat flips the gravity axis**,
so your sense of "forward" keeps rotating. Built to practice a clean game loop,
collision handling, and — the part that matters — keeping **game logic separate
from rendering** so it can be unit-tested.

**Live demo:** static site (deploy `index.html` to Vercel).

## Design
- `src/game.js` is the entire rules engine: pure, deterministic (injectable RNG),
  no DOM. `createGame` / `turn` / `step` are the whole API.
- `index.html` is just I/O: keyboard → `turn`, `requestAnimationFrame` → `step`,
  Canvas → draw. Swap the renderer without touching the rules.

## Run
```bash
npm test          # rules engine tests (node --test)
npm run serve     # http://localhost:8081
```

## What I learned / next
- Decoupling simulation from rendering makes a game testable.
- Next: fixed-timestep accumulator tuning, score persistence, and a true
  gravity mode where the snake drifts when idle.

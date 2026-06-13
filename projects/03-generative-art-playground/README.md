# 🎨 Generative Art Playground (#03)

Seedable, shareable generative art in the browser. Pick a style, type a seed,
get a deterministic artwork — same seed always renders the same image, and the
URL updates so any piece is a shareable link. Export to PNG.

**Live demo:** static site (deploy to Vercel — `index.html` at the root).

## Styles
- **flow-field** — particles advected through a noise field.
- **subdivision** — recursive Mondrian-style block splitting.
- **circle-pack** — greedy non-overlapping circle packing.

## Why it's built this way
- **Deterministic by construction.** All randomness flows through a seeded
  `mulberry32` PRNG (`src/rng.js`); a string seed is hashed (FNV-1a) to 32 bits.
  Reproducibility is what makes art *shareable* and *testable*.
- **Zero dependencies.** Pure Canvas + ES modules, so it deploys as a static
  site and the logic is unit-testable under Node's built-in test runner.

## Run
```bash
npm test          # unit tests for the PRNG (node --test, no deps)
npm run serve     # http://localhost:8080
```

## What I learned / next
- Building reproducible randomness as a first-class concern.
- Next: port the hot loops to **Rust + WASM** for heavier simulations, and add
  a flow-field variant driven by true Perlin noise.

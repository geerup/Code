# 🧵 Physics / Particle Sandbox (#18)

A real-time **Verlet integration** physics toy: points store their previous
position (so velocity is implicit), gravity is applied each step, and distance
constraints ("sticks") are satisfied by iterative relaxation — enough to
simulate a draggable cloth. The core is pure and deterministic, so the physics
is **unit-tested**, not just eyeballed.

## Why Verlet
Verlet integration is stable and dead-simple for constraint-based bodies: you
move points, then repeatedly nudge them back toward rest lengths. More relaxation
iterations = stiffer cloth. No velocity bookkeeping, no matrices.

## Tests (`test/physics.test.mjs`)
gravity pulls a point down · pinned points never move · a stretched stick
relaxes back to rest length · points stay in bounds · the sim is deterministic
for identical setups · grid wiring is correct.

## Run
```bash
npm test          # physics core (node --test)
npm run serve     # http://localhost:8086 — drag the cloth
```

## What I learned / next
- Verlet integration, constraint relaxation, and keeping a simulation
  deterministic (and therefore testable).
- Next: tearable cloth (remove over-stretched sticks), mouse "cutting", and
  rigid-body collisions.

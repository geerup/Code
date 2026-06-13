# 🏰 Procedural Dungeon Generator (#17)

Seeded **BSP (binary space partition)** dungeon generation. The map is
recursively split into regions, each region gets a room, and rooms are joined by
L-shaped corridors — all driven by a deterministic PRNG, so a seed always yields
the same dungeon.

Two implementations that share one algorithm:
- **Rust crate** (`src/`) — the reference implementation, a CLI, and the test
  suite (determinism, connectivity via flood fill, wall borders). **Zero deps.**
- **Browser port** (`web/`) — a Canvas visualizer (a JS port of the same
  SplitMix64 + BSP), deployable as a **static site**.

## Run
```bash
# Rust reference + tests
cargo test
cargo run -- --seed 42 --width 54 --height 22      # ASCII
cargo run -- --seed 42 --json                       # JSON (tiles + rooms)

# Browser visualizer
cd web && npm test && npm run serve                 # http://localhost:8083
```

## Notable tests
- **Reproducibility:** same seed → identical tiles & rooms.
- **Connectivity:** a flood fill from the first room must reach every other
  room — proving the corridor pass never leaves an island.

## What I learned / next
- BSP partitioning, seeded generation as a testable property, and keeping a Rust
  core and JS port in algorithmic lockstep.
- Next: compile the Rust crate to WASM (drop the JS port), add cellular-automata
  caves, and place doors/keys with a solvability guarantee.

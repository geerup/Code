// "One Button Ascent" — a game-jam micro-game on the theme ONE BUTTON.
// A flyer auto-scrolls; tap to flap upward, release to fall. Dodge gaps in
// scrolling walls. All rules live here, engine-free and deterministic (seeded
// obstacle stream), so the loop is unit-tested and the renderer is swappable.

export function createGame({ width = 360, height = 540, seed = 1 } = {}) {
  return {
    width, height,
    rng: mulberry32(seed >>> 0),
    bird: { y: height / 2, vy: 0 },
    gravity: 1400,
    flap: -380,
    flapping: false,
    walls: [],
    spawnTimer: 0,
    spawnEvery: 1.1,
    speed: 150,
    gap: 150,
    score: 0,
    time: 0,
    over: false,
  };
}

export function setFlap(state, down) {
  state.flapping = down;
}

function spawnWall(state) {
  const margin = 60;
  const gapY = margin + state.rng() * (state.height - state.gap - margin * 2);
  state.walls.push({ x: state.width, gapY, gapH: state.gap, passed: false });
}

export function step(state, dt) {
  if (state.over) return state;
  state.time += dt;

  // Vertical motion: gravity, plus upward thrust while the button is held.
  state.bird.vy += state.gravity * dt;
  if (state.flapping) state.bird.vy += state.flap * dt * 6;
  state.bird.y += state.bird.vy * dt;

  // Hitting the floor or ceiling ends the run.
  if (state.bird.y <= 0 || state.bird.y >= state.height) {
    state.bird.y = clamp(state.bird.y, 0, state.height);
    state.over = true;
    return state;
  }

  // Spawn + advance walls.
  state.spawnTimer += dt;
  if (state.spawnTimer >= state.spawnEvery) {
    state.spawnTimer -= state.spawnEvery;
    spawnWall(state);
  }
  const birdX = state.width * 0.3;
  for (const wall of state.walls) {
    wall.x -= state.speed * dt;
    // Score when a wall passes the bird.
    if (!wall.passed && wall.x + 20 < birdX) {
      wall.passed = true;
      state.score += 1;
    }
    // Collision: bird overlaps wall x-range but outside the gap.
    if (wall.x < birdX + 12 && wall.x + 40 > birdX - 12) {
      if (state.bird.y < wall.gapY || state.bird.y > wall.gapY + wall.gapH) {
        state.over = true;
      }
    }
  }
  state.walls = state.walls.filter((w) => w.x > -50);
  return state;
}

function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

// Seeded PRNG so an obstacle stream is reproducible (testable + fair daily runs).
export function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

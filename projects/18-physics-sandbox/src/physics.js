// A small Verlet-integration physics core: points carry their previous position
// (velocity is implicit), gravity is applied, and distance constraints ("sticks")
// are satisfied by iterative relaxation. Pure and deterministic so it's
// unit-testable; the Canvas demo just renders this state.

export class Point {
  constructor(x, y, pinned = false) {
    this.x = x; this.y = y;
    this.px = x; this.py = y; // previous position
    this.pinned = pinned;
  }
}

export class Stick {
  constructor(a, b, length = null) {
    this.a = a; this.b = b;
    this.length = length ?? Math.hypot(a.x - b.x, a.y - b.y);
  }
}

export class World {
  constructor({ width = 800, height = 600, gravity = 1500, bounce = 0.9, friction = 0.999 } = {}) {
    this.width = width; this.height = height;
    this.gravity = gravity; this.bounce = bounce; this.friction = friction;
    this.points = [];
    this.sticks = [];
  }

  addPoint(x, y, pinned = false) {
    const p = new Point(x, y, pinned);
    this.points.push(p);
    return p;
  }

  addStick(a, b, length = null) {
    const s = new Stick(a, b, length);
    this.sticks.push(s);
    return s;
  }

  // Integrate positions using Verlet: next = pos + (pos - prev)*friction + accel*dt^2.
  _integrate(dt) {
    for (const p of this.points) {
      if (p.pinned) continue;
      const vx = (p.x - p.px) * this.friction;
      const vy = (p.y - p.py) * this.friction;
      p.px = p.x; p.py = p.y;
      p.x += vx;
      p.y += vy + this.gravity * dt * dt;
    }
  }

  // Pull each stick's endpoints back to its rest length (half-correction each).
  _solveSticks() {
    for (const s of this.sticks) {
      const dx = s.b.x - s.a.x;
      const dy = s.b.y - s.a.y;
      const dist = Math.hypot(dx, dy) || 1e-6;
      const diff = (s.length - dist) / dist;
      const ox = dx * 0.5 * diff;
      const oy = dy * 0.5 * diff;
      if (!s.a.pinned) { s.a.x -= ox; s.a.y -= oy; }
      if (!s.b.pinned) { s.b.x += ox; s.b.y += oy; }
    }
  }

  // Keep points inside the box, reflecting velocity (encoded in prev position).
  _constrainBounds() {
    for (const p of this.points) {
      if (p.pinned) continue;
      const vx = p.x - p.px;
      const vy = p.y - p.py;
      if (p.x < 0) { p.x = 0; p.px = p.x + vx * this.bounce; }
      else if (p.x > this.width) { p.x = this.width; p.px = p.x + vx * this.bounce; }
      if (p.y < 0) { p.y = 0; p.py = p.y + vy * this.bounce; }
      else if (p.y > this.height) { p.y = this.height; p.py = p.y + vy * this.bounce; }
    }
  }

  // Advance the simulation by dt seconds (with `iterations` constraint passes).
  step(dt, iterations = 5) {
    this._integrate(dt);
    for (let i = 0; i < iterations; i++) {
      this._solveSticks();
      this._constrainBounds();
    }
  }
}

// Helper: build a rectangular cloth/grid of points + sticks for the demo & tests.
export function buildGrid(world, cols, rows, spacing, ox = 0, oy = 0) {
  const grid = [];
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const pinned = y === 0 && x % 2 === 0; // pin alternating top row
      grid.push(world.addPoint(ox + x * spacing, oy + y * spacing, pinned));
    }
  }
  const idx = (x, y) => y * cols + x;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      if (x < cols - 1) world.addStick(grid[idx(x, y)], grid[idx(x + 1, y)]);
      if (y < rows - 1) world.addStick(grid[idx(x, y)], grid[idx(x, y + 1)]);
    }
  }
  return grid;
}

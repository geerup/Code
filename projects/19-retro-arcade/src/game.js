// Pure game logic for "Gravity Snake" — a Snake variant with a twist:
// every apple you eat flips the gravity axis, so the board's "down" rotates.
// Logic is engine-free and fully unit-testable; rendering lives in index.html.

export const DIRS = {
  up: { x: 0, y: -1 },
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
};

const OPPOSITE = { up: 'down', down: 'up', left: 'right', right: 'left' };

export function createGame(cols = 20, rows = 20, rng = Math.random) {
  const state = {
    cols, rows, rng,
    snake: [{ x: 4, y: 10 }, { x: 3, y: 10 }, { x: 2, y: 10 }],
    dir: 'right',
    nextDir: 'right',
    apple: null,
    score: 0,
    gravity: 'right', // the twist: tracks the last flip axis (cosmetic + scoring)
    over: false,
  };
  placeApple(state);
  return state;
}

function placeApple(state) {
  const occupied = new Set(state.snake.map((s) => `${s.x},${s.y}`));
  const free = [];
  for (let y = 0; y < state.rows; y++)
    for (let x = 0; x < state.cols; x++)
      if (!occupied.has(`${x},${y}`)) free.push({ x, y });
  state.apple = free.length ? free[Math.floor(state.rng() * free.length)] : null;
  if (!state.apple) state.over = true; // board full = win/end
}

// Queue a direction change; ignore reversals into yourself.
export function turn(state, dir) {
  if (!DIRS[dir]) return;
  if (dir === OPPOSITE[state.dir]) return;
  state.nextDir = dir;
}

// Advance one tick. Returns the mutated state.
export function step(state) {
  if (state.over) return state;
  state.dir = state.nextDir;
  const d = DIRS[state.dir];
  const head = state.snake[0];
  const nx = head.x + d.x;
  const ny = head.y + d.y;

  // Wall or self collision ends the game.
  if (nx < 0 || ny < 0 || nx >= state.cols || ny >= state.rows) {
    state.over = true;
    return state;
  }
  if (state.snake.some((s) => s.x === nx && s.y === ny)) {
    state.over = true;
    return state;
  }

  state.snake.unshift({ x: nx, y: ny });
  if (state.apple && nx === state.apple.x && ny === state.apple.y) {
    state.score += 1;
    state.gravity = state.dir; // twist: gravity flips to your travel axis
    placeApple(state);
  } else {
    state.snake.pop();
  }
  return state;
}

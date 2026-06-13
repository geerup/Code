// Generative algorithms. Each takes (ctx, width, height, rng) and paints.
// Pure functions of the rng → identical seed yields identical art.

function pick(rng, arr) {
  return arr[Math.floor(rng() * arr.length)];
}

const PALETTES = [
  ['#0b132b', '#1c2541', '#3a506b', '#5bc0be', '#6fffe9'],
  ['#2b2d42', '#8d99ae', '#edf2f4', '#ef233c', '#d90429'],
  ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51'],
  ['#03071e', '#370617', '#9d0208', '#dc2f02', '#ffba08'],
  ['#10002b', '#5a189a', '#9d4edd', '#c77dff', '#e0aaff'],
];

// 1) Flow field — particles advected through Perlin-ish value noise.
export function flowField(ctx, w, h, rng) {
  const pal = pick(rng, PALETTES);
  ctx.fillStyle = pal[0];
  ctx.fillRect(0, 0, w, h);
  const grid = 24;
  const cols = Math.ceil(w / grid) + 1;
  const rows = Math.ceil(h / grid) + 1;
  const angles = [];
  for (let i = 0; i < cols * rows; i++) angles.push(rng() * Math.PI * 2);
  ctx.lineWidth = 1;
  const particles = 1200;
  for (let p = 0; p < particles; p++) {
    let x = rng() * w;
    let y = rng() * h;
    ctx.strokeStyle = pick(rng, pal.slice(1)) + '99';
    ctx.beginPath();
    ctx.moveTo(x, y);
    for (let step = 0; step < 60; step++) {
      const c = Math.min(cols - 1, Math.floor(x / grid));
      const r = Math.min(rows - 1, Math.floor(y / grid));
      const a = angles[r * cols + c];
      x += Math.cos(a) * 4;
      y += Math.sin(a) * 4;
      if (x < 0 || x > w || y < 0 || y > h) break;
      ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

// 2) Recursive subdivision (Mondrian-ish) — splits the canvas into blocks.
export function subdivide(ctx, w, h, rng) {
  const pal = pick(rng, PALETTES);
  ctx.fillStyle = pal[2];
  ctx.fillRect(0, 0, w, h);
  function rec(x, y, ww, hh, depth) {
    if (depth <= 0 || (ww < 60 && hh < 60) || rng() < 0.12) {
      ctx.fillStyle = pick(rng, pal) + 'ee';
      ctx.fillRect(x + 4, y + 4, ww - 8, hh - 8);
      return;
    }
    if (ww > hh) {
      const s = ww * (0.3 + rng() * 0.4);
      rec(x, y, s, hh, depth - 1);
      rec(x + s, y, ww - s, hh, depth - 1);
    } else {
      const s = hh * (0.3 + rng() * 0.4);
      rec(x, y, ww, s, depth - 1);
      rec(x, y + s, ww, hh - s, depth - 1);
    }
  }
  rec(0, 0, w, h, 7);
}

// 3) Circle packing — non-overlapping circles grown to fit gaps.
export function circlePack(ctx, w, h, rng) {
  const pal = pick(rng, PALETTES);
  ctx.fillStyle = pal[0];
  ctx.fillRect(0, 0, w, h);
  const circles = [];
  let tries = 0;
  while (circles.length < 500 && tries < 12000) {
    tries++;
    const x = rng() * w;
    const y = rng() * h;
    let r = 2;
    let ok = true;
    for (const c of circles) {
      const d = Math.hypot(c.x - x, c.y - y) - c.r;
      if (d < r) { ok = false; break; }
      r = Math.min(r, d);
    }
    if (!ok || r < 3) continue;
    r = Math.min(r, 60);
    circles.push({ x, y, r });
    ctx.beginPath();
    ctx.arc(x, y, r - 1, 0, Math.PI * 2);
    ctx.fillStyle = pick(rng, pal.slice(1)) + 'dd';
    ctx.fill();
  }
}

export const GENERATORS = {
  'flow-field': flowField,
  subdivision: subdivide,
  'circle-pack': circlePack,
};

export const GENERATOR_NAMES = Object.keys(GENERATORS);

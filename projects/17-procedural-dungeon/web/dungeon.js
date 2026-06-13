// Browser port of the Rust BSP dungeon generator (src/lib.rs). Same SplitMix64
// PRNG and same partition algorithm, so seeds line up conceptually. BigInt is
// used for 64-bit PRNG arithmetic.
const MASK = (1n << 64n) - 1n;

class Rng {
  constructor(seed) { this.state = BigInt(seed) & MASK; }
  next() {
    this.state = (this.state + 0x9E3779B97F4A7C15n) & MASK;
    let z = this.state;
    z = ((z ^ (z >> 30n)) * 0xBF58476D1CE4E5B9n) & MASK;
    z = ((z ^ (z >> 27n)) * 0x94D049BB133111EBn) & MASK;
    return (z ^ (z >> 31n)) & MASK;
  }
  range(low, high) { // [low, high)
    const span = BigInt(high - low);
    return low + Number(this.next() % span);
  }
}

function splitRegion(region, depth, rng, out) {
  const min = 7;
  if (depth === 0 || (region.w < min * 2 && region.h < min * 2)) { out.push(region); return; }
  let horizontal;
  if (region.w / region.h > 1.25) horizontal = false;
  else if (region.h / region.w > 1.25) horizontal = true;
  else horizontal = rng.next() % 2n === 0n;

  if (horizontal) {
    if (region.h < min * 2) { out.push(region); return; }
    const cut = rng.range(min, region.h - min + 1);
    splitRegion({ x: region.x, y: region.y, w: region.w, h: cut }, depth - 1, rng, out);
    splitRegion({ x: region.x, y: region.y + cut, w: region.w, h: region.h - cut }, depth - 1, rng, out);
  } else {
    if (region.w < min * 2) { out.push(region); return; }
    const cut = rng.range(min, region.w - min + 1);
    splitRegion({ x: region.x, y: region.y, w: cut, h: region.h }, depth - 1, rng, out);
    splitRegion({ x: region.x + cut, y: region.y, w: region.w - cut, h: region.h }, depth - 1, rng, out);
  }
}

export function generate(width, height, seed) {
  const rng = new Rng(seed);
  const tiles = new Uint8Array(width * height); // 0 wall, 1 floor
  const carve = (x, y) => { if (x >= 0 && y >= 0 && x < width && y < height) tiles[y * width + x] = 1; };

  const leaves = [];
  splitRegion({ x: 1, y: 1, w: width - 2, h: height - 2 }, 4, rng, leaves);

  const rooms = [];
  for (const leaf of leaves) {
    if (leaf.w < 4 || leaf.h < 4) continue;
    const rw = rng.range(3, Math.min(leaf.w, 12) + 1);
    const rh = rng.range(3, Math.min(leaf.h, 12) + 1);
    const rx = leaf.x + rng.range(0, Math.max(leaf.w - rw, 1));
    const ry = leaf.y + rng.range(0, Math.max(leaf.h - rh, 1));
    for (let yy = ry; yy < ry + rh; yy++) for (let xx = rx; xx < rx + rw; xx++) carve(xx, yy);
    rooms.push({ x: rx, y: ry, w: rw, h: rh });
  }

  for (let i = 1; i < rooms.length; i++) {
    const ax = rooms[i - 1].x + (rooms[i - 1].w >> 1), ay = rooms[i - 1].y + (rooms[i - 1].h >> 1);
    const bx = rooms[i].x + (rooms[i].w >> 1), by = rooms[i].y + (rooms[i].h >> 1);
    for (let x = Math.min(ax, bx); x <= Math.max(ax, bx); x++) carve(x, ay);
    for (let y = Math.min(ay, by); y <= Math.max(ay, by); y++) carve(bx, y);
  }

  return { width, height, tiles, rooms };
}

// Pure tilemap model: the data structure and (de)serialization behind the
// editor. Kept DOM-free so it's unit-testable and reusable by games (#09/#14).

export const TILES = [
  { id: 0, name: 'empty', color: 'transparent' },
  { id: 1, name: 'wall', color: '#5b5b6b' },
  { id: 2, name: 'floor', color: '#2a9d8f' },
  { id: 3, name: 'water', color: '#3a7ca5' },
  { id: 4, name: 'spawn', color: '#e9c46a' },
  { id: 5, name: 'goal', color: '#e76f51' },
];

export class TileMap {
  constructor(width, height, fill = 0) {
    this.width = width;
    this.height = height;
    this.data = new Array(width * height).fill(fill);
  }

  inBounds(x, y) {
    return x >= 0 && y >= 0 && x < this.width && y < this.height;
  }

  get(x, y) {
    return this.inBounds(x, y) ? this.data[y * this.width + x] : -1;
  }

  set(x, y, tile) {
    if (this.inBounds(x, y)) this.data[y * this.width + x] = tile;
    return this;
  }

  // Flood fill the contiguous region of like tiles starting at (x, y).
  fill(x, y, tile) {
    const target = this.get(x, y);
    if (target === tile || target === -1) return this;
    const stack = [[x, y]];
    while (stack.length) {
      const [cx, cy] = stack.pop();
      if (this.get(cx, cy) !== target) continue;
      this.set(cx, cy, tile);
      stack.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
    }
    return this;
  }

  resize(width, height) {
    const next = new TileMap(width, height, 0);
    for (let y = 0; y < Math.min(height, this.height); y++)
      for (let x = 0; x < Math.min(width, this.width); x++)
        next.set(x, y, this.get(x, y));
    this.width = width;
    this.height = height;
    this.data = next.data;
    return this;
  }

  count(tile) {
    return this.data.reduce((n, t) => n + (t === tile ? 1 : 0), 0);
  }

  toJSON() {
    return { width: this.width, height: this.height, data: this.data.slice() };
  }

  static fromJSON(obj) {
    if (!obj || typeof obj.width !== 'number' || !Array.isArray(obj.data))
      throw new Error('invalid level JSON');
    if (obj.data.length !== obj.width * obj.height)
      throw new Error('data length does not match dimensions');
    const m = new TileMap(obj.width, obj.height);
    m.data = obj.data.slice();
    return m;
  }
}

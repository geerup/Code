//! Seeded BSP (binary space partition) dungeon generator.
//!
//! The map is recursively split into sub-regions; each leaf gets a room, and
//! sibling rooms are joined by corridors. Everything is driven by a seeded PRNG,
//! so a given seed always produces the same dungeon — reproducible and testable
//! with **zero external dependencies**.

/// A tiny deterministic PRNG (SplitMix64). Good enough for level generation.
pub struct Rng {
    state: u64,
}

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng { state: seed.wrapping_add(0x9E3779B97F4A7C15) }
    }

    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }

    /// Uniform integer in [low, high). Requires high > low.
    pub fn range(&mut self, low: i32, high: i32) -> i32 {
        debug_assert!(high > low);
        let span = (high - low) as u64;
        low + (self.next_u64() % span) as i32
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Tile {
    Wall,
    Floor,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Room {
    pub x: i32,
    pub y: i32,
    pub w: i32,
    pub h: i32,
}

impl Room {
    pub fn center(&self) -> (i32, i32) {
        (self.x + self.w / 2, self.y + self.h / 2)
    }
}

pub struct Dungeon {
    pub width: i32,
    pub height: i32,
    pub tiles: Vec<Tile>,
    pub rooms: Vec<Room>,
}

impl Dungeon {
    pub fn at(&self, x: i32, y: i32) -> Tile {
        if x < 0 || y < 0 || x >= self.width || y >= self.height {
            return Tile::Wall;
        }
        self.tiles[(y * self.width + x) as usize]
    }

    fn carve(&mut self, x: i32, y: i32) {
        if x >= 0 && y >= 0 && x < self.width && y < self.height {
            self.tiles[(y * self.width + x) as usize] = Tile::Floor;
        }
    }

    /// Count floor tiles — handy for tests and stats.
    pub fn floor_count(&self) -> usize {
        self.tiles.iter().filter(|t| **t == Tile::Floor).count()
    }

    /// Render the dungeon as ASCII ('#' wall, '.' floor).
    pub fn to_ascii(&self) -> String {
        let mut s = String::with_capacity(((self.width + 1) * self.height) as usize);
        for y in 0..self.height {
            for x in 0..self.width {
                s.push(if self.at(x, y) == Tile::Floor { '.' } else { '#' });
            }
            s.push('\n');
        }
        s
    }
}

struct Region {
    x: i32,
    y: i32,
    w: i32,
    h: i32,
}

/// Generate a dungeon of the given size from a seed.
pub fn generate(width: i32, height: i32, seed: u64) -> Dungeon {
    let mut rng = Rng::new(seed);
    let mut dungeon = Dungeon {
        width,
        height,
        tiles: vec![Tile::Wall; (width * height) as usize],
        rooms: Vec::new(),
    };

    // Recursively partition, collecting leaf regions.
    let mut leaves: Vec<Region> = Vec::new();
    split(Region { x: 1, y: 1, w: width - 2, h: height - 2 }, 4, &mut rng, &mut leaves);

    // Place a room inside each leaf.
    for leaf in &leaves {
        if leaf.w < 4 || leaf.h < 4 {
            continue;
        }
        let rw = rng.range(3, leaf.w.min(12) + 1);
        let rh = rng.range(3, leaf.h.min(12) + 1);
        let rx = leaf.x + rng.range(0, (leaf.w - rw).max(1));
        let ry = leaf.y + rng.range(0, (leaf.h - rh).max(1));
        let room = Room { x: rx, y: ry, w: rw, h: rh };
        for yy in room.y..room.y + room.h {
            for xx in room.x..room.x + room.w {
                dungeon.carve(xx, yy);
            }
        }
        dungeon.rooms.push(room);
    }

    // Connect consecutive rooms with L-shaped corridors.
    for pair in dungeon.rooms.clone().windows(2) {
        let (ax, ay) = pair[0].center();
        let (bx, by) = pair[1].center();
        for x in ax.min(bx)..=ax.max(bx) {
            dungeon.carve(x, ay);
        }
        for y in ay.min(by)..=ay.max(by) {
            dungeon.carve(bx, y);
        }
    }

    dungeon
}

fn split(region: Region, depth: u32, rng: &mut Rng, out: &mut Vec<Region>) {
    let min_size = 7;
    if depth == 0 || (region.w < min_size * 2 && region.h < min_size * 2) {
        out.push(region);
        return;
    }
    // Prefer splitting the longer axis to avoid thin slivers.
    let horizontal = if region.w as f32 / region.h as f32 > 1.25 {
        false
    } else if region.h as f32 / region.w as f32 > 1.25 {
        true
    } else {
        rng.next_u64() % 2 == 0
    };

    if horizontal {
        if region.h < min_size * 2 {
            out.push(region);
            return;
        }
        let cut = rng.range(min_size, region.h - min_size + 1);
        split(Region { x: region.x, y: region.y, w: region.w, h: cut }, depth - 1, rng, out);
        split(Region { x: region.x, y: region.y + cut, w: region.w, h: region.h - cut }, depth - 1, rng, out);
    } else {
        if region.w < min_size * 2 {
            out.push(region);
            return;
        }
        let cut = rng.range(min_size, region.w - min_size + 1);
        split(Region { x: region.x, y: region.y, w: cut, h: region.h }, depth - 1, rng, out);
        split(Region { x: region.x + cut, y: region.y, w: region.w - cut, h: region.h }, depth - 1, rng, out);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rng_is_deterministic() {
        let mut a = Rng::new(123);
        let mut b = Rng::new(123);
        for _ in 0..1000 {
            assert_eq!(a.next_u64(), b.next_u64());
        }
    }

    #[test]
    fn rng_range_within_bounds() {
        let mut rng = Rng::new(7);
        for _ in 0..10_000 {
            let v = rng.range(5, 10);
            assert!((5..10).contains(&v));
        }
    }

    #[test]
    fn same_seed_same_dungeon() {
        let a = generate(60, 40, 42);
        let b = generate(60, 40, 42);
        assert_eq!(a.tiles, b.tiles);
        assert_eq!(a.rooms, b.rooms);
    }

    #[test]
    fn different_seeds_differ() {
        let a = generate(60, 40, 1);
        let b = generate(60, 40, 2);
        assert_ne!(a.tiles, b.tiles);
    }

    #[test]
    fn produces_rooms_and_floor() {
        let d = generate(80, 50, 99);
        assert!(!d.rooms.is_empty(), "expected at least one room");
        assert!(d.floor_count() > 50, "expected carved floor space");
    }

    #[test]
    fn border_is_walls() {
        let d = generate(40, 30, 5);
        for x in 0..d.width {
            assert_eq!(d.at(x, 0), Tile::Wall);
            assert_eq!(d.at(x, d.height - 1), Tile::Wall);
        }
    }

    #[test]
    fn rooms_are_connected() {
        // Flood fill from the first room must reach every other room's center.
        let d = generate(80, 50, 7);
        let start = d.rooms[0].center();
        let mut seen = vec![false; (d.width * d.height) as usize];
        let mut stack = vec![start];
        while let Some((x, y)) = stack.pop() {
            if x < 0 || y < 0 || x >= d.width || y >= d.height {
                continue;
            }
            let idx = (y * d.width + x) as usize;
            if seen[idx] || d.at(x, y) != Tile::Floor {
                continue;
            }
            seen[idx] = true;
            stack.extend_from_slice(&[(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]);
        }
        for room in &d.rooms {
            let (cx, cy) = room.center();
            assert!(seen[(cy * d.width + cx) as usize], "room at {:?} unreachable", (cx, cy));
        }
    }
}

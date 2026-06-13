//! CLI: print a procedurally generated dungeon as ASCII or JSON.
//!
//!   dungeon                       # default 80x40, random-ish seed
//!   dungeon --seed 42 --json      # deterministic, JSON output
//!   dungeon --width 100 --height 50 --seed 7

use procedural_dungeon::{generate, Tile};
use std::time::{SystemTime, UNIX_EPOCH};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mut width = 80i32;
    let mut height = 40i32;
    let mut seed: u64 = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(1);
    let mut json = false;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--seed" => { seed = args.get(i + 1).and_then(|s| s.parse().ok()).unwrap_or(seed); i += 1; }
            "--width" => { width = args.get(i + 1).and_then(|s| s.parse().ok()).unwrap_or(width); i += 1; }
            "--height" => { height = args.get(i + 1).and_then(|s| s.parse().ok()).unwrap_or(height); i += 1; }
            "--json" => { json = true; }
            _ => {}
        }
        i += 1;
    }

    let d = generate(width, height, seed);

    if json {
        let tiles: Vec<u8> = d.tiles.iter().map(|t| if *t == Tile::Floor { 1 } else { 0 }).collect();
        let rooms: Vec<String> = d
            .rooms
            .iter()
            .map(|r| format!("[{},{},{},{}]", r.x, r.y, r.w, r.h))
            .collect();
        let tile_str: Vec<String> = tiles.iter().map(|t| t.to_string()).collect();
        println!(
            "{{\"width\":{},\"height\":{},\"seed\":{},\"rooms\":[{}],\"tiles\":[{}]}}",
            width, height, seed, rooms.join(","), tile_str.join(",")
        );
    } else {
        eprintln!("seed {} — {} rooms, {} floor tiles", seed, d.rooms.len(), d.floor_count());
        print!("{}", d.to_ascii());
    }
}

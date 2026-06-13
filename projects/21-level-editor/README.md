# 🧱 Level Editor (#21)

A grid-based tile/level editor in the browser: paint tiles with a brush or
flood-fill bucket, then **export the level as JSON** for a game to load (it feeds
the AI Game Master #09 and NPC dialogue demos #14). Import JSON back to keep
editing.

## Design
The interesting part is `src/tilemap.js` — a **DOM-free tilemap model** with
`set/get`, flood `fill`, `resize`, and round-trip JSON (de)serialization. Because
it's pure data, it's fully unit-tested and reusable by any game, while
`index.html` is just the Canvas UI on top.

## Run
```bash
npm test          # tilemap model tests (node --test)
npm run serve     # http://localhost:8084
```

## Level JSON
```json
{ "width": 24, "height": 16, "data": [0,1,1,2, ...] }
```
`data` is row-major tile ids (see the `TILES` palette).

## What I learned / next
- Separating an editor's *model* from its *view*; flood fill; safe deserialization.
- Next: multi-layer maps, undo/redo via a command stack, and a tileset image
  importer.

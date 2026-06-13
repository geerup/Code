"""Game-spec schema + validation/repair.

The bridge turns a natural-language description into a *structured, playable*
level spec (JSON). The schema and validator live here so the LLM's output can be
validated, repaired, and trusted before a game loads it. Keeping this pure makes
the whole pipeline testable without a model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TILE_LEGEND = {
    0: "empty",
    1: "wall",
    2: "floor",
    3: "hazard",
    4: "spawn",
    5: "goal",
    6: "coin",
}
VALID_TILES = set(TILE_LEGEND)


class ValidationError(Exception):
    pass


@dataclass
class LevelSpec:
    name: str
    width: int
    height: int
    tiles: list[int]
    theme: str = "dungeon"
    entities: list[dict] = field(default_factory=list)

    def tile_at(self, x: int, y: int) -> int:
        return self.tiles[y * self.width + x]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "theme": self.theme,
            "tiles": self.tiles,
            "entities": self.entities,
            "legend": TILE_LEGEND,
        }


def validate(obj: dict) -> LevelSpec:
    """Validate a raw dict into a LevelSpec, raising ValidationError on problems."""
    for key in ("width", "height", "tiles"):
        if key not in obj:
            raise ValidationError(f"missing required field: {key}")
    w, h = obj["width"], obj["height"]
    if not isinstance(w, int) or not isinstance(h, int) or w <= 0 or h <= 0:
        raise ValidationError("width/height must be positive integers")
    tiles = obj["tiles"]
    if not isinstance(tiles, list) or len(tiles) != w * h:
        raise ValidationError(f"tiles length {len(tiles)} != width*height {w * h}")
    if any(t not in VALID_TILES for t in tiles):
        raise ValidationError("tiles contain invalid ids")
    spec = LevelSpec(
        name=obj.get("name", "Untitled"),
        width=w,
        height=h,
        tiles=list(tiles),
        theme=obj.get("theme", "dungeon"),
        entities=obj.get("entities", []),
    )
    _check_playable(spec)
    return spec


def _check_playable(spec: LevelSpec) -> None:
    """A playable level needs exactly the basics: a spawn and a reachable goal."""
    if spec.tiles.count(4) < 1:
        raise ValidationError("level must contain a spawn (tile 4)")
    if spec.tiles.count(5) < 1:
        raise ValidationError("level must contain a goal (tile 5)")
    if not _goal_reachable(spec):
        raise ValidationError("goal is not reachable from spawn")


def _goal_reachable(spec: LevelSpec) -> bool:
    """BFS over non-wall tiles from the spawn to a goal."""
    start = spec.tiles.index(4)
    sx, sy = start % spec.width, start // spec.width
    seen = [False] * len(spec.tiles)
    stack = [(sx, sy)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= spec.width or y >= spec.height:
            continue
        i = y * spec.width + x
        if seen[i] or spec.tiles[i] == 1:  # wall blocks
            continue
        seen[i] = True
        if spec.tiles[i] == 5:
            return True
        stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return False

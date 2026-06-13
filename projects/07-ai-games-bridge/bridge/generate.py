"""Pipeline: natural-language description -> validated LevelSpec.

The LLM is asked to emit strict JSON. We parse (tolerating code fences), then
validate; on failure we deterministically *repair* the level so the bridge
always yields something playable — the key reliability trick when wiring LLMs to
game engines.
"""
from __future__ import annotations

import json
import re
from typing import Protocol

from .schema import LevelSpec, ValidationError, validate


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        ...


SYSTEM = """You are a level designer. Given a description, output ONLY a JSON object:
{"name": str, "width": int (8-24), "height": int (6-16), "theme": str,
 "tiles": [int...] row-major of length width*height, "entities": [{"type","x","y"}]}
Tile ids: 0 empty,1 wall,2 floor,3 hazard,4 spawn,5 goal,6 coin.
Include exactly one spawn (4) and one goal (5), with a wall border. No prose."""


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of an LLM reply that may be fenced or chatty."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw = fence.group(1) if fence else text
    brace = re.search(r"\{.*\}", raw, re.DOTALL)
    if not brace:
        raise ValidationError("no JSON object found in LLM output")
    return json.loads(brace.group(0))


def repair(obj: dict) -> LevelSpec:
    """Coerce a near-miss into a guaranteed-playable level.

    Strategy: take the requested size (clamped), lay an open floor with a wall
    border, then place spawn top-left and goal bottom-right so a path exists.
    Preserves coins/hazards from the model where they fit on floor tiles.
    """
    w = _clamp(int(obj.get("width", 12)), 8, 24)
    h = _clamp(int(obj.get("height", 8)), 6, 16)
    tiles = [0] * (w * h)
    for y in range(h):
        for x in range(w):
            border = x == 0 or y == 0 or x == w - 1 or y == h - 1
            tiles[y * w + x] = 1 if border else 2

    # Carry over coins/hazards that land on interior floor.
    src = obj.get("tiles")
    if isinstance(src, list) and len(src) == w * h:
        for i, t in enumerate(src):
            if t in (3, 6) and tiles[i] == 2:
                tiles[i] = t

    tiles[w + 1] = 4               # spawn just inside top-left
    tiles[(h - 2) * w + (w - 2)] = 5  # goal just inside bottom-right
    return validate({
        "name": obj.get("name", "Repaired Level"),
        "width": w, "height": h, "theme": obj.get("theme", "dungeon"),
        "tiles": tiles, "entities": obj.get("entities", []),
    })


def generate(llm: LLM, description: str) -> LevelSpec:
    """Full pipeline with validate-then-repair fallback."""
    raw = llm.complete(SYSTEM, description)
    try:
        return validate(_extract_json(raw))
    except (ValidationError, json.JSONDecodeError, ValueError):
        # Repair from whatever we could parse, else from an empty hint dict.
        try:
            parsed = _extract_json(raw)
        except Exception:
            parsed = {}
        return repair(parsed)


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))

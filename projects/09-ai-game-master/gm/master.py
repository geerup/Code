"""The Game Master: turns the world state + a player action into narration and
validated state changes by prompting an LLM for a strict JSON response.

Contract — the model must reply with a JSON object:
    {"narration": str, "effects": [{"op": "move"|"take"|"drop"|"set", ...}]}
The engine parses it tolerantly, applies only valid effects (World.apply_all),
and falls back to plain narration if the JSON is unusable.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from .world import World


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        ...


SYSTEM = """You are the Game Master of a text adventure. Given the world state and
the player's action, respond with ONLY a JSON object:
{"narration": "2-4 vivid sentences", "effects": [ ... ]}
Valid effects:
  {"op":"move","to":"<exit direction or room id>"}
  {"op":"take","item":"<item present in the room>"}
  {"op":"drop","item":"<item in inventory>"}
  {"op":"set","flag":"<name>","value":true|false}
Only use exits and items that exist in the provided state. No prose outside JSON."""


@dataclass
class Turn:
    narration: str
    applied_effects: list[dict]
    snapshot: dict


def _extract_json(text: str) -> dict:
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    raw = fence.group(1) if fence else text
    brace = re.search(r"\{.*\}", raw, re.DOTALL)
    if not brace:
        raise ValueError("no JSON object found")
    return json.loads(brace.group(0))


class GameMaster:
    def __init__(self, llm: LLM, world: World):
        self.llm = llm
        self.world = world

    def _prompt(self, action: str) -> str:
        return json.dumps({"state": self.world.snapshot(), "action": action})

    def act(self, action: str) -> Turn:
        raw = self.llm.complete(SYSTEM, self._prompt(action))
        try:
            data = _extract_json(raw)
            narration = str(data.get("narration", "")).strip() or "..."
            effects = data.get("effects", [])
        except (ValueError, json.JSONDecodeError):
            # Model didn't produce JSON; treat the whole reply as narration only.
            narration, effects = raw.strip(), []

        applied = self.world.apply_all(effects)
        self.world.log.append(f"> {action}")
        self.world.log.append(narration)
        return Turn(narration=narration, applied_effects=applied, snapshot=self.world.snapshot())

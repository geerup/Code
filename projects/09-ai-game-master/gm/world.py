"""Authoritative game world + the effects an action can have.

The key design choice: **the engine owns the truth, not the LLM.** The model
proposes narration plus structured *effects*; the engine validates and applies
them to this state. A hallucinated move to a nonexistent room is rejected, so
the game can't be talked into an impossible state.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class InvalidEffect(Exception):
    pass


@dataclass
class Location:
    id: str
    name: str
    description: str
    exits: dict[str, str] = field(default_factory=dict)  # direction -> location id
    items: list[str] = field(default_factory=list)


@dataclass
class World:
    locations: dict[str, Location]
    start: str
    current: str = ""
    inventory: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.current:
            self.current = self.start
        if self.current not in self.locations:
            raise ValueError(f"start location {self.current!r} does not exist")

    def here(self) -> Location:
        return self.locations[self.current]

    def snapshot(self) -> dict:
        loc = self.here()
        return {
            "location": {"id": loc.id, "name": loc.name, "description": loc.description,
                          "exits": loc.exits, "items": loc.items},
            "inventory": list(self.inventory),
            "flags": dict(self.flags),
        }

    # --- effect application (the only way state changes) ----------------------

    def apply(self, effect: dict) -> None:
        op = effect.get("op")
        if op == "move":
            self._move(effect.get("to", ""))
        elif op == "take":
            self._take(effect.get("item", ""))
        elif op == "drop":
            self._drop(effect.get("item", ""))
        elif op == "set":
            self.flags[effect["flag"]] = bool(effect.get("value", True))
        else:
            raise InvalidEffect(f"unknown op: {op!r}")

    def apply_all(self, effects: list[dict]) -> list[dict]:
        """Apply a list of effects, skipping invalid ones; returns the applied set."""
        applied = []
        for eff in effects or []:
            try:
                self.apply(eff)
                applied.append(eff)
            except InvalidEffect:
                continue  # reject the model's impossible move, keep playing
        return applied

    def _move(self, dest: str) -> None:
        # Accept either an exit direction from the current room or a room id
        # that is reachable via an exit (never an arbitrary teleport).
        here = self.here()
        if dest in here.exits:
            self.current = here.exits[dest]
        elif dest in here.exits.values():
            self.current = dest
        else:
            raise InvalidEffect(f"cannot move to {dest!r} from {here.id!r}")

    def _take(self, item: str) -> None:
        here = self.here()
        if item not in here.items:
            raise InvalidEffect(f"no {item!r} here to take")
        here.items.remove(item)
        self.inventory.append(item)

    def _drop(self, item: str) -> None:
        if item not in self.inventory:
            raise InvalidEffect(f"{item!r} not in inventory")
        self.inventory.remove(item)
        self.here().items.append(item)


def demo_world() -> World:
    """A tiny starter map used by the server and tests."""
    return World(
        start="clearing",
        locations={
            "clearing": Location("clearing", "Forest Clearing",
                "Sunlight filters through the trees. A path leads north into a cave.",
                exits={"north": "cave"}, items=["torch"]),
            "cave": Location("cave", "Dark Cave",
                "Damp and pitch black. A faint glow seeps from a crack to the east.",
                exits={"south": "clearing", "east": "chamber"}),
            "chamber": Location("chamber", "Glowing Chamber",
                "Crystals line the walls. An ancient chest sits in the center.",
                exits={"west": "cave"}, items=["golden key"]),
        },
    )

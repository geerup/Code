"""Describe a level in English; get a validated, playable JSON level + ASCII preview.

    python cli.py "a cramped dungeon with hazards around the goal"
"""
from __future__ import annotations

import argparse
import json
import urllib.request

from bridge import generate, TILE_LEGEND

GLYPHS = {0: " ", 1: "#", 2: ".", 3: "^", 4: "@", 5: "X", 6: "o"}


class OllamaLLM:
    def __init__(self, model="llama3.1", base_url="http://localhost:11434"):
        self.model, self.base_url = model, base_url.rstrip("/")

    def complete(self, system, user):
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"model": self.model, "stream": False, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            return json.loads(r.read())["message"]["content"]


def ascii_preview(spec) -> str:
    rows = []
    for y in range(spec.height):
        rows.append("".join(GLYPHS.get(spec.tile_at(x, y), "?") for x in range(spec.width)))
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("description")
    ap.add_argument("--model", default="llama3.1")
    ap.add_argument("--json", action="store_true", help="print the level JSON")
    args = ap.parse_args()

    spec = generate(OllamaLLM(args.model), args.description)
    print(f"# {spec.name}  ({spec.width}x{spec.height}, theme={spec.theme})")
    print(f"# legend: {TILE_LEGEND}\n")
    print(ascii_preview(spec))
    if args.json:
        print("\n" + json.dumps(spec.to_dict()))


if __name__ == "__main__":
    main()

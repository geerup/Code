import os
import sys
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge import validate, ValidationError, generate, repair  # noqa: E402


class ScriptedLLM:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, user):
        return self.reply


def good_level():
    # 8x6 with wall border, spawn (4) and goal (5) on an open floor.
    w, h = 8, 6
    tiles = []
    for y in range(h):
        for x in range(w):
            tiles.append(1 if x in (0, w - 1) or y in (0, h - 1) else 2)
    tiles[w + 1] = 4
    tiles[(h - 2) * w + (w - 2)] = 5
    return {"name": "Test", "width": w, "height": h, "tiles": tiles}


class TestValidation(unittest.TestCase):
    def test_valid_level_passes(self):
        spec = validate(good_level())
        self.assertEqual(spec.width, 8)
        self.assertIn(4, spec.tiles)

    def test_wrong_tile_count_rejected(self):
        bad = good_level()
        bad["tiles"] = bad["tiles"][:-1]
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_missing_goal_rejected(self):
        bad = good_level()
        bad["tiles"] = [4 if t == 5 else t for t in bad["tiles"]]  # remove goal
        with self.assertRaises(ValidationError):
            validate(bad)

    def test_unreachable_goal_rejected(self):
        bad = good_level()
        # Wall off the goal's neighbors.
        gi = bad["tiles"].index(5)
        w = bad["width"]
        for n in (gi - 1, gi + 1, gi - w, gi + w):
            if 0 <= n < len(bad["tiles"]):
                bad["tiles"][n] = 1
        with self.assertRaises(ValidationError):
            validate(bad)


class TestPipeline(unittest.TestCase):
    def test_generate_accepts_valid_llm_json(self):
        llm = ScriptedLLM("```json\n" + json.dumps(good_level()) + "\n```")
        spec = generate(llm, "a small test room")
        self.assertEqual(spec.name, "Test")

    def test_generate_repairs_garbage_into_playable(self):
        spec = generate(ScriptedLLM("totally not json, sorry!"), "a spooky cave")
        # Repair must yield a valid, reachable level.
        validate(spec.to_dict())
        self.assertIn(4, spec.tiles)
        self.assertIn(5, spec.tiles)

    def test_generate_repairs_wrong_size(self):
        llm = ScriptedLLM(json.dumps({"width": 10, "height": 8, "tiles": [0, 1, 2]}))
        spec = generate(llm, "mismatched")
        self.assertEqual(len(spec.tiles), spec.width * spec.height)

    def test_repair_preserves_coins_when_they_fit(self):
        obj = {"width": 8, "height": 6, "tiles": [6] * 48}  # all coins
        spec = repair(obj)
        self.assertIn(6, spec.tiles)  # some coins survive on interior floor


if __name__ == "__main__":
    unittest.main()

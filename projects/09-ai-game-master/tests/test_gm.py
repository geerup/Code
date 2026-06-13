import os
import sys
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gm import World, demo_world, GameMaster, ScriptedLLM, InvalidEffect  # noqa: E402


class TestWorld(unittest.TestCase):
    def test_move_via_exit_direction(self):
        w = demo_world()
        w.apply({"op": "move", "to": "north"})
        self.assertEqual(w.current, "cave")

    def test_move_to_unreachable_rejected(self):
        w = demo_world()  # at clearing; chamber is not a direct exit
        with self.assertRaises(InvalidEffect):
            w.apply({"op": "move", "to": "chamber"})

    def test_take_and_drop(self):
        w = demo_world()
        w.apply({"op": "take", "item": "torch"})
        self.assertIn("torch", w.inventory)
        self.assertNotIn("torch", w.here().items)
        w.apply({"op": "drop", "item": "torch"})
        self.assertIn("torch", w.here().items)

    def test_take_absent_item_rejected(self):
        w = demo_world()
        with self.assertRaises(InvalidEffect):
            w.apply({"op": "take", "item": "sword"})

    def test_apply_all_skips_invalid_keeps_valid(self):
        w = demo_world()
        applied = w.apply_all([
            {"op": "take", "item": "torch"},     # valid
            {"op": "move", "to": "chamber"},     # invalid (not an exit)
            {"op": "set", "flag": "brave", "value": True},  # valid
        ])
        self.assertEqual(len(applied), 2)
        self.assertIn("torch", w.inventory)
        self.assertTrue(w.flags["brave"])
        self.assertEqual(w.current, "clearing")  # invalid move had no effect


class TestGameMaster(unittest.TestCase):
    def test_applies_effects_from_llm_json(self):
        reply = json.dumps({"narration": "You stride north into darkness.",
                            "effects": [{"op": "move", "to": "north"}]})
        gm = GameMaster(ScriptedLLM([reply]), demo_world())
        turn = gm.act("go north")
        self.assertEqual(gm.world.current, "cave")
        self.assertEqual(turn.snapshot["location"]["id"], "cave")
        self.assertEqual(len(turn.applied_effects), 1)

    def test_rejects_hallucinated_effect(self):
        reply = json.dumps({"narration": "You teleport to the chamber!",
                            "effects": [{"op": "move", "to": "chamber"}]})
        gm = GameMaster(ScriptedLLM([reply]), demo_world())
        turn = gm.act("teleport")
        self.assertEqual(gm.world.current, "clearing")  # engine held the line
        self.assertEqual(turn.applied_effects, [])

    def test_handles_fenced_json(self):
        reply = "```json\n" + json.dumps({"narration": "Grabbed it.",
                 "effects": [{"op": "take", "item": "torch"}]}) + "\n```"
        gm = GameMaster(ScriptedLLM([reply]), demo_world())
        gm.act("take torch")
        self.assertIn("torch", gm.world.inventory)

    def test_non_json_reply_becomes_narration(self):
        gm = GameMaster(ScriptedLLM(["The wind howls ominously."]), demo_world())
        turn = gm.act("listen")
        self.assertEqual(turn.narration, "The wind howls ominously.")
        self.assertEqual(turn.applied_effects, [])


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import Agent, ScriptedLLM, default_registry  # noqa: E402
from agent.tools import calculator, Registry  # noqa: E402


class TestTools(unittest.TestCase):
    def test_calculator_basic(self):
        self.assertEqual(calculator("2 * (3 + 4)"), "14")

    def test_calculator_rejects_code(self):
        self.assertTrue(calculator("__import__('os')").startswith("error"))

    def test_registry_unknown_tool(self):
        r = default_registry()
        self.assertIn("unknown tool", r.run("nope", "x"))

    def test_manifest_lists_tools(self):
        r = default_registry()
        self.assertIn("calculator", r.manifest())


class TestAgentLoop(unittest.TestCase):
    def test_single_tool_then_final(self):
        llm = ScriptedLLM(["ACTION: calculator(10 * 5)", "FINAL: the answer is 50"])
        agent = Agent(llm, default_registry())
        result = agent.run("compute 10*5")
        self.assertTrue(result.completed)
        self.assertEqual(result.answer, "the answer is 50")
        # The tool observation should have been 50.
        tool_steps = [s for s in result.steps if s.action == "calculator"]
        self.assertEqual(tool_steps[0].observation, "50")

    def test_multi_step(self):
        llm = ScriptedLLM([
            "ACTION: calculator(2+2)",
            "ACTION: reverse(hello)",
            "FINAL: done",
        ])
        result = Agent(llm, default_registry()).run("multi")
        self.assertTrue(result.completed)
        self.assertEqual(len([s for s in result.steps if s.action]), 2)

    def test_immediate_final(self):
        result = Agent(ScriptedLLM(["FINAL: 42"]), default_registry()).run("q")
        self.assertEqual(result.answer, "42")

    def test_max_steps_guard(self):
        # Always emits an action, never FINAL -> must stop at max_steps.
        llm = ScriptedLLM(["ACTION: calculator(1+1)"] * 20)
        result = Agent(llm, default_registry(), max_steps=3).run("loop")
        self.assertFalse(result.completed)
        self.assertIn("max steps", result.answer)
        self.assertEqual(len(result.steps), 3)

    def test_non_protocol_reply_becomes_answer(self):
        result = Agent(ScriptedLLM(["just some prose"]), default_registry()).run("q")
        self.assertEqual(result.answer, "just some prose")


if __name__ == "__main__":
    unittest.main()

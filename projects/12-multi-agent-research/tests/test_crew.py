import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crew import run_crew, ScriptedLLM, static_search  # noqa: E402

CORPUS = {
    "Solar Basics": "solar panels convert sunlight into electricity using photovoltaic cells",
    "Wind Power": "wind turbines generate electricity from moving air and wind",
    "Grid Storage": "batteries store electricity for the grid to balance supply and demand",
}


class TestCrew(unittest.TestCase):
    def test_pipeline_produces_structured_report(self):
        llm = ScriptedLLM(by_role={
            "Planner": ["how do solar panels work\nhow is electricity stored"],
            "Writer": ["Solar panels use photovoltaic cells [Solar Basics]. Storage uses batteries [Grid Storage]."],
            "Critic": ["APPROVED"],
        })
        report = run_crew(llm, static_search(CORPUS), "How does renewable energy work?")
        self.assertEqual(len(report.sub_questions), 2)
        self.assertTrue(report.evidence)
        self.assertEqual(report.final, report.draft)  # approved -> no revision
        self.assertIn("Solar Basics", report.citations())

    def test_researcher_finds_relevant_sources(self):
        llm = ScriptedLLM(by_role={
            "Planner": ["how do wind turbines generate electricity"],
            "Writer": ["draft"],
            "Critic": ["APPROVED"],
        })
        report = run_crew(llm, static_search(CORPUS), "wind energy")
        titles = [t for ev in report.evidence for t, _ in ev.sources]
        self.assertIn("Wind Power", titles)

    def test_critic_triggers_one_revision(self):
        llm = ScriptedLLM(by_role={
            "Planner": ["q1"],
            "Writer": ["first draft, unsupported", "revised draft addressing critique"],
            "Critic": ["Claim X is unsupported by evidence."],
        })
        report = run_crew(llm, static_search(CORPUS), "topic")
        self.assertNotEqual(report.critique.strip().upper(), "APPROVED")
        self.assertEqual(report.final, "revised draft addressing critique")

    def test_planner_falls_back_to_question(self):
        llm = ScriptedLLM(by_role={"Planner": [""], "Writer": ["d"], "Critic": ["APPROVED"]})
        report = run_crew(llm, static_search(CORPUS), "lonely question")
        self.assertEqual(report.sub_questions, ["lonely question"])

    def test_each_agent_role_is_invoked(self):
        llm = ScriptedLLM(by_role={
            "Planner": ["q1\nq2"], "Writer": ["d"], "Critic": ["APPROVED"],
        })
        run_crew(llm, static_search(CORPUS), "q")
        roles_seen = {r for (sys_prompt, _) in llm.calls for r in ("Planner", "Writer", "Critic") if r in sys_prompt}
        self.assertEqual(roles_seen, {"Planner", "Writer", "Critic"})


if __name__ == "__main__":
    unittest.main()

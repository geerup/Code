import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evalkit import score, run, load_cases, Case  # noqa: E402
from evalkit.cases import f1_tokens, numeric  # noqa: E402
from evalkit.llm import ScriptedLLM  # noqa: E402
from evalkit.runner import judge_score  # noqa: E402


class TestMetrics(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(score("exact", "Paris", "Paris "), 1.0)
        self.assertEqual(score("exact", "paris", "Paris"), 0.0)

    def test_contains_case_insensitive(self):
        self.assertEqual(score("contains", "The capital is Paris.", "paris"), 1.0)

    def test_numeric_extracts_number(self):
        self.assertEqual(numeric("The answer is 51.", "51"), 1.0)
        self.assertEqual(numeric("about 50", "51"), 0.0)

    def test_f1_partial_credit(self):
        s = f1_tokens("hello there world", "hello world")
        self.assertGreater(s, 0.0)
        self.assertLess(s, 1.0)

    def test_unknown_metric_raises(self):
        with self.assertRaises(ValueError):
            score("bogus", "a", "b")


class TestRunner(unittest.TestCase):
    def test_run_scores_each_case(self):
        cases = [
            Case("a", "q1", "yes", "contains"),
            Case("b", "q2", "42", "numeric"),
        ]
        model = ScriptedLLM({"q1": "the answer is yes", "q2": "42"})
        report = run(model, cases)
        self.assertEqual(report.total if hasattr(report, "total") else len(report.results), 2)
        self.assertEqual(report.mean, 1.0)
        self.assertEqual(report.passed, 2)

    def test_judge_metric(self):
        judge = ScriptedLLM(default="0.8")
        case = Case("j", "explain x", "reference", "judge")
        self.assertAlmostEqual(judge_score(judge, case, "candidate"), 0.8)

    def test_report_serialization(self):
        report = run(ScriptedLLM(default="51"), [Case("m", "q", "51", "numeric")])
        d = report.to_dict()
        self.assertEqual(d["total"], 1)
        self.assertIn("cases", d)


class TestDataset(unittest.TestCase):
    def test_load_sample(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cases = load_cases(os.path.join(here, "datasets", "basics.jsonl"))
        self.assertEqual(len(cases), 5)
        self.assertTrue(all(c.id for c in cases))


if __name__ == "__main__":
    unittest.main()

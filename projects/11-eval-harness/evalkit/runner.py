"""Run a model over a dataset, score each case, and aggregate results.

Includes an LLM-as-judge metric: when a case can't be checked mechanically, a
judge model rates the answer 0-1. The judge is just another ``LLM`` so it's
mocked in tests.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Protocol

from .cases import Case, score


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str:  # pragma: no cover
        ...


@dataclass
class CaseResult:
    id: str
    output: str
    score: float
    metric: str


@dataclass
class Report:
    results: list[CaseResult] = field(default_factory=list)

    @property
    def mean(self) -> float:
        return sum(r.score for r in self.results) / len(self.results) if self.results else 0.0

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.score >= 0.999)

    def to_dict(self) -> dict:
        return {
            "mean_score": round(self.mean, 4),
            "passed": self.passed,
            "total": len(self.results),
            "cases": [vars(r) for r in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


JUDGE_SYSTEM = (
    "You are a strict grader. Given a QUESTION, a REFERENCE answer, and a "
    "CANDIDATE answer, reply with only a number from 0 to 1 for how well the "
    "candidate matches the reference in meaning."
)


def judge_score(judge: LLM, case: Case, output: str) -> float:
    user = f"QUESTION: {case.prompt}\nREFERENCE: {case.expected}\nCANDIDATE: {output}\nScore:"
    raw = judge.complete(JUDGE_SYSTEM, user)
    m = re.search(r"0?\.\d+|[01]", raw)
    return max(0.0, min(1.0, float(m.group()))) if m else 0.0


def run(model: LLM, cases: list[Case], system: str = "", judge: LLM | None = None) -> Report:
    report = Report()
    for case in cases:
        output = model.complete(system, case.prompt)
        if case.metric == "judge":
            if judge is None:
                raise ValueError(f"case {case.id} needs a judge model")
            s = judge_score(judge, case, output)
        else:
            s = score(case.metric, output, case.expected)
        report.results.append(CaseResult(case.id, output, round(s, 4), case.metric))
    return report

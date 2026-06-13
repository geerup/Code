"""Eval datasets and scoring metrics.

A test case pairs an input prompt with an expectation. Metrics score a model's
output against that expectation and return a float in [0, 1]. Keeping metrics
pure makes the whole harness deterministic and unit-testable.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Case:
    id: str
    prompt: str
    expected: str
    metric: str = "exact"  # one of METRICS


# --- metrics: (output, expected) -> score in [0,1] ----------------------------

def exact(output: str, expected: str) -> float:
    return 1.0 if output.strip() == expected.strip() else 0.0


def contains(output: str, expected: str) -> float:
    return 1.0 if expected.strip().lower() in output.lower() else 0.0


def regex(output: str, expected: str) -> float:
    return 1.0 if re.search(expected, output) else 0.0


def numeric(output: str, expected: str) -> float:
    """Extract the first number from the output and compare to expected."""
    m = re.search(r"-?\d+(?:\.\d+)?", output)
    if not m:
        return 0.0
    try:
        return 1.0 if abs(float(m.group()) - float(expected)) < 1e-6 else 0.0
    except ValueError:
        return 0.0


def f1_tokens(output: str, expected: str) -> float:
    """Token-level F1 — partial credit for overlapping words."""
    o = output.lower().split()
    e = expected.lower().split()
    if not o or not e:
        return 0.0
    common = 0
    pool = list(e)
    for tok in o:
        if tok in pool:
            pool.remove(tok)
            common += 1
    if common == 0:
        return 0.0
    precision = common / len(o)
    recall = common / len(e)
    return 2 * precision * recall / (precision + recall)


METRICS: dict[str, Callable[[str, str], float]] = {
    "exact": exact,
    "contains": contains,
    "regex": regex,
    "numeric": numeric,
    "f1": f1_tokens,
}


def score(metric: str, output: str, expected: str) -> float:
    fn = METRICS.get(metric)
    if fn is None:
        raise ValueError(f"unknown metric '{metric}' (have {sorted(METRICS)})")
    return fn(output, expected)


def load_cases(path: str | Path) -> list[Case]:
    """Load a JSONL dataset of cases."""
    cases: list[Case] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        cases.append(Case(d["id"], d["prompt"], str(d["expected"]), d.get("metric", "exact")))
    return cases

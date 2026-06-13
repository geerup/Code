# 📊 Prompt-Eval / LLM-Judge Harness (#11)

A tiny but real evaluation harness for LLM prompts: define cases in JSONL, run a
model over them, score with mechanical metrics **or an LLM-as-judge**, and emit
a JSON + HTML report you can gate CI on (regression detection).

## Metrics (`evalkit/cases.py`)
`exact` · `contains` · `regex` · `numeric` (extracts a number) · `f1` (token
overlap, partial credit) · `judge` (a model rates 0–1 vs. a reference).

## Dataset format (JSONL)
```json
{"id": "math-1", "prompt": "What is 17 * 3?", "expected": "51", "metric": "numeric"}
{"id": "explain", "prompt": "What is recursion?", "expected": "a function that calls itself", "metric": "judge"}
```

## Run
```bash
python run_eval.py datasets/basics.jsonl --model llama3.1 --out report --threshold 0.6
python -m unittest discover -s tests      # offline (scripted model)
```
`--threshold` makes the process exit non-zero when the mean score drops — drop
it into CI to catch prompt/model regressions.

## Why it matters
Shipping LLM features without evals is flying blind. This shows the core loop:
**datasets → metrics → aggregate score → regression gate**, with the judge model
mocked in tests so the harness itself is deterministic.

## What I learned / next
- Designing graded metrics and an LLM-judge; keeping evals reproducible.
- Next: pairwise A/B comparison of two models, confidence intervals, and a
  historical trend dashboard.

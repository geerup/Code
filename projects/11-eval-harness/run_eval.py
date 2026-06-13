"""Run an eval dataset against an Ollama model and emit a JSON + HTML report.

    python run_eval.py datasets/basics.jsonl --model llama3.1 --out report
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

from evalkit import load_cases, run
from evalkit.llm import OllamaLLM


def html_report(report) -> str:
    rows = []
    for r in report.results:
        color = "#1b5e20" if r.score >= 0.999 else ("#7a4f01" if r.score > 0 else "#7a0010")
        rows.append(
            f"<tr><td>{html.escape(r.id)}</td><td>{r.metric}</td>"
            f"<td style='background:{color};color:#fff'>{r.score:.2f}</td>"
            f"<td><pre>{html.escape(r.output[:300])}</pre></td></tr>"
        )
    return f"""<!doctype html><meta charset=utf-8><title>Eval report</title>
<style>body{{font-family:system-ui;background:#0d1117;color:#ddd;padding:24px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #333;padding:8px;text-align:left;vertical-align:top}}
pre{{margin:0;white-space:pre-wrap}}</style>
<h1>Eval report</h1>
<p>Mean score <b>{report.mean:.3f}</b> &middot; passed {report.passed}/{len(report.results)}</p>
<table><tr><th>case</th><th>metric</th><th>score</th><th>output</th></tr>{''.join(rows)}</table>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--model", default="llama3.1")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--out", default="report")
    ap.add_argument("--threshold", type=float, default=0.0, help="fail if mean < threshold")
    args = ap.parse_args()

    cases = load_cases(args.dataset)
    model = OllamaLLM(args.model, args.url)
    report = run(model, cases, judge=model)  # model also acts as judge

    Path(f"{args.out}.json").write_text(report.to_json())
    Path(f"{args.out}.html").write_text(html_report(report))
    print(report.to_json())
    print(f"\nWrote {args.out}.json and {args.out}.html")
    if report.mean < args.threshold:
        raise SystemExit(f"FAIL: mean {report.mean:.3f} < threshold {args.threshold}")


if __name__ == "__main__":
    main()

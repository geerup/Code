# 🧑‍🔬 Multi-Agent Research Crew (#12) ★

A small **multi-agent system** where specialized agents collaborate to produce a
cited research report — the orchestration pattern behind "agent crews," kept
small enough to read and **fully testable offline**.

## The crew
```
Planner    → splits the question into focused sub-questions
Researcher → gathers evidence per sub-question via a search tool
Writer     → drafts a report grounded ONLY in the gathered evidence, with [citations]
Critic     → flags unsupported claims; if not APPROVED, Writer revises once
```
Each agent is a **role-tagged LLM call**; the orchestrator (`run_crew`) wires
them and manages the single critique→revision loop, returning a structured
`Report` (sub-questions, evidence, draft, critique, final, citations).

## Why it's testable
The LLM and the search tool are both injected. Tests use a `ScriptedLLM` (canned
output per role) and an offline keyword `static_search` over an in-memory corpus,
so the full pipeline — including the critic-triggered revision — runs in
milliseconds with no network.

## Run
```bash
python cli.py "How does retrieval-augmented generation work?"   # needs Ollama
python -m unittest discover -s tests                             # offline
```

## What I learned / next
- Decomposing a task across roles, grounding writers in retrieved evidence, and
  using a critic loop to reduce hallucination.
- Next: parallel researchers (async), real web search + fetching, and a shared
  scratchpad/blackboard so agents build on each other's findings.

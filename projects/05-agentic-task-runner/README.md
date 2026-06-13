# 🤖 Agentic Task Runner (#05)

A compact **ReAct-style agent**: the model plans, calls tools, observes results,
and loops until it can answer. The whole "planner → tool-use → execute" cycle in
~80 readable lines, with a sandboxed tool registry. Runs on a **local Ollama**
model; the LLM is behind a protocol so the loop is tested with **no network**.

## How it works
Each turn the model emits exactly one of:
```
ACTION: tool_name(argument)      # gather a fact
FINAL: answer                    # finish
```
The runner parses the action, runs the tool, appends `OBSERVATION:`, and repeats
(up to `max_steps`). See `agent/runner.py`.

**Built-in tools** (`agent/tools.py`): `calculator` (AST-sandboxed, no `eval`),
`word_count`, `reverse`. Adding a tool is one `register(...)` call.

## Run
```bash
python cli.py "What is 12 * (7 + 3)?" --verbose     # needs Ollama running
python -m unittest discover -s tests                 # offline, scripted LLM
```

## Why this design
- **Provider-agnostic.** `OllamaLLM` for real use, `ScriptedLLM` for tests.
- **Safe by default.** Tools are pure and sandboxed, so the loop is CI-safe.
- **Guardrails.** Hard `max_steps` cap prevents infinite tool loops.

## What I learned / next
- The ReAct pattern and why structured action parsing + step caps matter.
- Next: parallel tool calls, a retrieval tool wired to project #04, and
  streaming intermediate steps to a UI.

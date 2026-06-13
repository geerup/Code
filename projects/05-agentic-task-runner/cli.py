"""CLI entrypoint: run the agent against a task using a local Ollama model.

    python cli.py "What is 12 * (7 + 3), and how many words are in this task?"
"""
from __future__ import annotations

import argparse

from agent import Agent, OllamaLLM, default_registry


def main() -> None:
    ap = argparse.ArgumentParser(description="ReAct agent with a small tool set")
    ap.add_argument("task", help="the task to solve")
    ap.add_argument("--model", default="llama3.1")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--verbose", action="store_true", help="print each step")
    args = ap.parse_args()

    agent = Agent(OllamaLLM(args.model, args.url), default_registry(), args.max_steps)
    result = agent.run(args.task)

    if args.verbose:
        for i, step in enumerate(result.steps, 1):
            print(f"--- step {i} ---")
            print(step.thought)
            if step.observation is not None:
                print(f"OBSERVATION: {step.observation}")
    print("\n=== ANSWER ===")
    print(result.answer)


if __name__ == "__main__":
    main()

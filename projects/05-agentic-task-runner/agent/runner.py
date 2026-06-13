"""A minimal ReAct-style agent loop.

The model is prompted to emit, on each turn, either:

    ACTION: <tool_name>(<argument>)

or a final answer:

    FINAL: <answer>

The runner parses the action, executes the tool, appends the observation, and
loops until the model returns FINAL or ``max_steps`` is reached. This is the
core "planner -> tool-use -> execute" pattern behind agent frameworks, kept
small enough to read in one sitting.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .llm import LLM
from .tools import Registry

ACTION_RE = re.compile(r"ACTION:\s*([a-zA-Z_]\w*)\s*\((.*)\)\s*$", re.DOTALL)
FINAL_RE = re.compile(r"FINAL:\s*(.*)", re.DOTALL)

SYSTEM_TEMPLATE = """You are a tool-using agent. Solve the user's task step by step.
On each turn respond with EXACTLY ONE of:
  ACTION: tool_name(argument)
  FINAL: your answer
Available tools:
{tools}
Use ACTION to gather facts, then FINAL to answer. Keep arguments on one line."""


@dataclass
class Step:
    thought: str
    action: str | None
    argument: str | None
    observation: str | None


@dataclass
class Result:
    answer: str
    steps: list[Step] = field(default_factory=list)
    completed: bool = False  # True if the model produced a FINAL answer


class Agent:
    def __init__(self, llm: LLM, registry: Registry, max_steps: int = 6):
        self.llm = llm
        self.registry = registry
        self.max_steps = max_steps

    def run(self, task: str) -> Result:
        system = SYSTEM_TEMPLATE.format(tools=self.registry.manifest())
        transcript = f"Task: {task}\n"
        result = Result(answer="")

        for _ in range(self.max_steps):
            reply = self.llm.complete(system, transcript).strip()

            final = FINAL_RE.search(reply)
            if final and (not ACTION_RE.search(reply) or final.start() < ACTION_RE.search(reply).start()):
                result.answer = final.group(1).strip()
                result.completed = True
                result.steps.append(Step(reply, None, None, None))
                return result

            m = ACTION_RE.search(reply)
            if not m:
                # Model didn't follow the protocol; treat the text as the answer.
                result.answer = reply
                result.steps.append(Step(reply, None, None, None))
                return result

            tool_name, arg = m.group(1), m.group(2).strip()
            observation = self.registry.run(tool_name, arg)
            result.steps.append(Step(reply, tool_name, arg, observation))
            transcript += f"{reply}\nOBSERVATION: {observation}\n"

        result.answer = "stopped: reached max steps"
        return result

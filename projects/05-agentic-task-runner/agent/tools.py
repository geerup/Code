"""Tool registry. Each tool is a named, documented callable the agent may
invoke with a single string argument and that returns a string observation.

Tools are intentionally pure/sandboxed so the agent loop is safe to run in CI.
"""
from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from typing import Callable

# --- safe arithmetic evaluator (no eval/exec) ---------------------------------

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


def calculator(expr: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4)'."""
    try:
        return str(_safe_eval(ast.parse(expr, mode="eval")))
    except Exception as e:  # noqa: BLE001 - report any parse/eval failure to the agent
        return f"error: {e}"


def word_count(text: str) -> str:
    """Count words in the given text."""
    return str(len(text.split()))


def reverse(text: str) -> str:
    """Reverse the given text."""
    return text[::-1]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    fn: Callable[[str], str]


class Registry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, fn: Callable[[str], str]) -> None:
        self._tools[name] = Tool(name, description, fn)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def manifest(self) -> str:
        """Human/LLM-readable list of tools for the system prompt."""
        return "\n".join(f"- {t.name}: {t.description}" for t in self._tools.values())

    def run(self, name: str, arg: str) -> str:
        tool = self.get(name)
        if tool is None:
            return f"error: unknown tool '{name}' (available: {', '.join(self.names())})"
        return tool.fn(arg)


def default_registry() -> Registry:
    r = Registry()
    r.register("calculator", "evaluate arithmetic, e.g. calculator(2*(3+4))", calculator)
    r.register("word_count", "count words in text", word_count)
    r.register("reverse", "reverse a string", reverse)
    return r

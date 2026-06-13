"""The crew: specialized agents that collaborate to produce a cited report.

Pipeline (orchestrated in `run_crew`):
    Planner   -> breaks the question into sub-questions
    Researcher-> gathers evidence per sub-question via a search tool
    Writer    -> drafts a report grounded in the gathered evidence
    Critic    -> flags unsupported claims; Writer revises once

Each agent is just a role-tagged LLM call, so the whole flow is deterministic
and testable with a ScriptedLLM + an offline search tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLM, SearchTool


@dataclass
class Evidence:
    sub_question: str
    sources: list[tuple[str, str]]  # (title, snippet)


@dataclass
class Report:
    question: str
    sub_questions: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    draft: str = ""
    critique: str = ""
    final: str = ""

    def citations(self) -> list[str]:
        titles: list[str] = []
        for ev in self.evidence:
            for title, _ in ev.sources:
                if title not in titles:
                    titles.append(title)
        return titles


def _planner(llm: LLM, question: str, max_subs: int) -> list[str]:
    system = "ROLE=Planner. Break the user's question into 2-4 focused sub-questions, one per line. No numbering."
    raw = llm.complete(system, question)
    subs = [ln.strip(" -•\t") for ln in raw.splitlines() if ln.strip()]
    return subs[:max_subs] or [question]


def _researcher(search: SearchTool, sub_questions: list[str]) -> list[Evidence]:
    out: list[Evidence] = []
    for sq in sub_questions:
        out.append(Evidence(sub_question=sq, sources=search(sq)))
    return out


def _format_evidence(evidence: list[Evidence]) -> str:
    lines = []
    for ev in evidence:
        lines.append(f"## {ev.sub_question}")
        for title, snippet in ev.sources:
            lines.append(f"[{title}] {snippet}")
        if not ev.sources:
            lines.append("(no sources found)")
    return "\n".join(lines)


def _writer(llm: LLM, question: str, evidence: list[Evidence], critique: str = "") -> str:
    system = ("ROLE=Writer. Write a concise, well-structured report answering the question "
              "using ONLY the provided evidence. Cite sources inline as [Title].")
    user = f"QUESTION: {question}\n\nEVIDENCE:\n{_format_evidence(evidence)}"
    if critique:
        user += f"\n\nREVISE addressing this critique:\n{critique}"
    return llm.complete(system, user)


def _critic(llm: LLM, draft: str, evidence: list[Evidence]) -> str:
    system = ("ROLE=Critic. Identify any claims in the draft not supported by the evidence, "
              "or missing citations. If the draft is well-supported, reply exactly 'APPROVED'.")
    user = f"DRAFT:\n{draft}\n\nEVIDENCE:\n{_format_evidence(evidence)}"
    return llm.complete(system, user)


def run_crew(llm: LLM, search: SearchTool, question: str, max_subs: int = 4) -> Report:
    """Run the full multi-agent pipeline and return a structured Report."""
    report = Report(question=question)
    report.sub_questions = _planner(llm, question, max_subs)
    report.evidence = _researcher(search, report.sub_questions)
    report.draft = _writer(llm, question, report.evidence)
    report.critique = _critic(llm, report.draft, report.evidence)

    if report.critique.strip().upper() == "APPROVED":
        report.final = report.draft
    else:
        # One revision round incorporating the critic's feedback.
        report.final = _writer(llm, question, report.evidence, critique=report.critique)
    return report

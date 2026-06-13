"""Run the research crew on a question over a small local corpus (offline) or
wire in a real web search. Uses a local Ollama model.

    python cli.py "How does retrieval-augmented generation work?"
"""
from __future__ import annotations

import argparse

from crew import run_crew, OllamaLLM, static_search

# A tiny built-in corpus so the demo works fully offline.
CORPUS = {
    "RAG Overview": "retrieval augmented generation combines a retriever and a language model to answer questions grounded in documents with citations",
    "Embeddings": "embeddings map text into vectors so semantic similarity becomes cosine distance for retrieval",
    "Vector Stores": "a vector store indexes embeddings for fast nearest neighbor search used by retrievers",
    "Agents": "agents plan, call tools, and iterate to complete multi step tasks autonomously",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--model", default="llama3.1")
    args = ap.parse_args()

    report = run_crew(OllamaLLM(args.model), static_search(CORPUS), args.question)
    print(f"# {report.question}\n")
    print("## Sub-questions")
    for s in report.sub_questions:
        print(f"- {s}")
    print("\n## Report\n")
    print(report.final)
    print("\n## Sources")
    for c in report.citations():
        print(f"- {c}")


if __name__ == "__main__":
    main()

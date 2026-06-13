"""Semantic code search over a directory.

    python search.py --root . "where do we parse the unified diff"
    python search.py --root . --embedder ollama "vector cosine similarity"
"""
from __future__ import annotations

import argparse

from codesearch import HashingEmbedder, OllamaEmbedder, Index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--root", default=".")
    ap.add_argument("--embedder", choices=["hashing", "ollama"], default="hashing")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    embedder = OllamaEmbedder() if args.embedder == "ollama" else HashingEmbedder()
    index = Index(embedder)
    n = index.build(args.root)
    print(f"indexed {n} chunks from {args.root}\n")

    for hit in index.search(args.query, args.k):
        print(f"{hit.score:.3f}  {hit.path}:{hit.start_line}-{hit.end_line}")
        for line in hit.preview.splitlines():
            print(f"      {line}")
        print()


if __name__ == "__main__":
    main()

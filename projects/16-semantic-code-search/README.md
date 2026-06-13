# 🔎 Semantic Code Search (#16)

Search a codebase by *meaning*, not just substring. Point it at a directory; it
chunks the source by line windows, embeds each chunk, and ranks chunks against
your natural-language query by cosine similarity — returning `file:line-range`
hits with previews.

## Usage
```bash
python search.py --root . "where do we parse the unified diff"
python search.py --root . --embedder ollama "cosine similarity over vectors"
python -m unittest discover -s tests      # offline (hashing embedder)
```

## Design
- **Pluggable embeddings.** `HashingEmbedder` (feature-hashing bag-of-subwords,
  L2-normalized, deterministic, zero-dep) makes indexing and tests run offline;
  `OllamaEmbedder` (`nomic-embed-text`) gives real neural quality. Search code
  depends only on the `Embedder` protocol.
- **Identifier-aware tokenizer.** `getUserName` → `get user name`, so queries in
  English match camelCase/snake_case code.
- **Chunk → line range.** Sliding windows map every hit back to exact lines.

This is the retrieval half of RAG (#04) applied to code, and it reuses the same
cosine-ranking idea as the from-scratch vector engine (#08).

## What I learned / next
- Feature hashing as a no-dependency embedding baseline; chunking strategy.
- Next: persist the index, incremental re-indexing on file change, and an
  approximate-NN index (HNSW) for large repos.

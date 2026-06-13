# 🧮 Vector Search Engine from Scratch (#08)

The machinery underneath RAG and semantic search, built from first principles in
Go: dense-vector similarity with two indexes — **exact** brute-force and
**approximate** LSH — plus the recall/speed trade-off measured in tests.

## What's inside
- `vec/vector.go` — dot product, L2 norm, cosine, normalization.
- `vec/index.go` — `FlatIndex`: exact, O(n)-per-query brute force. The ground
  truth.
- `vec/lsh.go` — `LSHIndex`: **random-hyperplane locality-sensitive hashing**.
  Each of L tables hashes a vector to a K-bit sign signature; queries only score
  candidates that collide in a bucket → sub-linear on average.

## The interesting test
`TestLSHRecallAgainstFlat` builds 2,000 clustered 32-d vectors (20 clusters —
the realistic shape of real embeddings) and asserts the approximate index
recovers **≥70% of the exact top-10** — quantifying the accuracy you trade for
speed. Other tests pin exact correctness and exact-match retrieval.

## Run
```bash
go test ./...                       # includes the recall benchmark-style test
go run ./cmd/vsearch "fast cars"    # exact vs LSH on toy documents
```

## What I learned / next
- How cosine similarity, normalization, and LSH actually work; recall as a
  measurable property, not a vibe.
- Next: HNSW graph index for higher recall at scale, product quantization for
  memory, and mmap-backed persistence (ties into #04 and #16).

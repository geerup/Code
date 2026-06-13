# 🔍 LLM Code-Review CLI (#06)

A single-binary Go CLI that reads a `git diff` and prints an LLM code review —
correctness bugs, security issues, simplifications. Drops into a pre-push hook
or CI step. Uses a **local Ollama** model by default (free, private), but the
model is behind an interface so it's fully testable offline.

**Distribution:** `go build` → static binary → GitHub Releases.

## Usage
```bash
go build -o review ./cmd/review

git diff origin/main... | ./review        # review a branch
./review --staged                          # review staged changes
./review --summary                         # model-free +/- summary
git diff | ./review --model qwen2.5-coder  # pick a model
```

## Architecture
- `internal/gitdiff` — a small unified-diff parser (files → hunks → lines).
- `internal/llm` — `Client` interface; `Ollama` (HTTP) for real use, `Static`
  for tests. Swapping providers is a one-line change.
- `internal/review` — builds the prompt, renders summaries, orchestrates the call.
- `cmd/review` — flags, stdin/git plumbing.

The seam that matters: review logic depends on the `llm.Client` interface, so
every package is unit-tested with **no network and no model**.

## Test
```bash
go test ./...
```

## What I learned / next
- Parsing unified diffs; designing for an injectable LLM boundary.
- Next: stream tokens to the terminal, post inline comments to a PR via the
  GitHub API, and add `--format=json` for CI gating.

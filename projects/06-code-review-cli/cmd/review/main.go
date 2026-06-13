// Command review reads a unified diff (from stdin or `git diff`) and prints an
// LLM-generated code review. Designed to drop into a pre-push hook or CI.
//
//	git diff origin/main... | review
//	review --staged
package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"

	"github.com/portfolio/code-review-cli/internal/gitdiff"
	"github.com/portfolio/code-review-cli/internal/llm"
	"github.com/portfolio/code-review-cli/internal/review"
)

func main() {
	var (
		staged  = flag.Bool("staged", false, "review staged changes (git diff --cached)")
		model   = flag.String("model", "llama3.1", "Ollama model name")
		baseURL = flag.String("url", "http://localhost:11434", "Ollama base URL")
		summary = flag.Bool("summary", false, "print a model-free summary only")
	)
	flag.Parse()

	raw, err := readDiff(*staged)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error reading diff:", err)
		os.Exit(1)
	}
	files := gitdiff.Parse(raw)

	if *summary {
		fmt.Println(review.Summary(files))
		return
	}

	fmt.Fprintln(os.Stderr, "→", review.Summary(files))
	client := llm.NewOllama(*baseURL, *model)
	out, err := review.Run(context.Background(), client, files)
	if err != nil {
		fmt.Fprintln(os.Stderr, "review failed:", err)
		os.Exit(1)
	}
	fmt.Println(out)
}

// readDiff pulls a diff from stdin if piped, otherwise shells out to git.
func readDiff(staged bool) (string, error) {
	if fi, _ := os.Stdin.Stat(); (fi.Mode() & os.ModeCharDevice) == 0 {
		b, err := io.ReadAll(os.Stdin)
		if err != nil {
			return "", err
		}
		if len(b) > 0 {
			return string(b), nil
		}
	}
	args := []string{"diff"}
	if staged {
		args = append(args, "--cached")
	}
	out, err := exec.Command("git", args...).Output()
	return string(out), err
}

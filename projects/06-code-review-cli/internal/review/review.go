// Package review turns parsed diffs into an LLM prompt and renders the result.
package review

import (
	"context"
	"fmt"
	"strings"

	"github.com/portfolio/code-review-cli/internal/gitdiff"
	"github.com/portfolio/code-review-cli/internal/llm"
)

const systemPrompt = `You are a precise, senior code reviewer. Review the unified
diff. Focus on correctness bugs, security issues, and clear simplifications.
Be concise. For each finding output a line:
- <file>:<approx line> — <severity: bug|security|style|nit> — <comment>
If the change looks good, say "LGTM" and one sentence why.`

// BuildPrompt renders the changed files into a compact, line-tagged prompt.
func BuildPrompt(files []gitdiff.FileDiff) string {
	var b strings.Builder
	for _, f := range files {
		fmt.Fprintf(&b, "### %s (+%d/-%d)\n", f.Path, f.Added(), f.Removed())
		for _, h := range f.Hunks {
			b.WriteString(h.Header)
			b.WriteByte('\n')
			for _, l := range h.Lines {
				b.WriteByte(l.Kind)
				b.WriteString(l.Text)
				b.WriteByte('\n')
			}
		}
		b.WriteByte('\n')
	}
	return b.String()
}

// Summary is a quick, model-free overview of the change set.
func Summary(files []gitdiff.FileDiff) string {
	var added, removed int
	for _, f := range files {
		added += f.Added()
		removed += f.Removed()
	}
	return fmt.Sprintf("%d file(s) changed, +%d/-%d lines", len(files), added, removed)
}

// Run sends the diff to the model and returns its review.
func Run(ctx context.Context, c llm.Client, files []gitdiff.FileDiff) (string, error) {
	if len(files) == 0 {
		return "No changes to review.", nil
	}
	return c.Complete(ctx, systemPrompt, BuildPrompt(files))
}

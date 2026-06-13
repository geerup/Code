package review

import (
	"context"
	"strings"
	"testing"

	"github.com/portfolio/code-review-cli/internal/gitdiff"
	"github.com/portfolio/code-review-cli/internal/llm"
)

func sampleFiles() []gitdiff.FileDiff {
	return gitdiff.Parse(`diff --git a/a.go b/a.go
--- a/a.go
+++ b/a.go
@@ -1,1 +1,2 @@
 package a
+var X = 1
`)
}

func TestBuildPromptIncludesPathAndChanges(t *testing.T) {
	p := BuildPrompt(sampleFiles())
	if !strings.Contains(p, "a.go") {
		t.Error("prompt missing file path")
	}
	if !strings.Contains(p, "+var X = 1") {
		t.Error("prompt missing added line")
	}
}

func TestSummaryCountsLines(t *testing.T) {
	if got := Summary(sampleFiles()); !strings.Contains(got, "+1/-0") {
		t.Errorf("unexpected summary: %q", got)
	}
}

func TestRunUsesInjectedClient(t *testing.T) {
	out, err := Run(context.Background(), llm.Static{Reply: "LGTM"}, sampleFiles())
	if err != nil {
		t.Fatal(err)
	}
	if out != "LGTM" {
		t.Errorf("want LGTM, got %q", out)
	}
}

func TestRunEmptyDiff(t *testing.T) {
	out, _ := Run(context.Background(), llm.Static{Reply: "x"}, nil)
	if !strings.Contains(out, "No changes") {
		t.Errorf("want no-changes message, got %q", out)
	}
}

package gitdiff

import "testing"

const sample = `diff --git a/main.go b/main.go
index 1111111..2222222 100644
--- a/main.go
+++ b/main.go
@@ -1,4 +1,5 @@
 package main
-import "fmt"
+import "log"
+import "os"
 func main() {}
diff --git a/util.go b/util.go
index 3333333..4444444 100644
--- a/util.go
+++ b/util.go
@@ -10,2 +10,2 @@
-old line
+new line
`

func TestParseFindsBothFiles(t *testing.T) {
	files := Parse(sample)
	if len(files) != 2 {
		t.Fatalf("want 2 files, got %d", len(files))
	}
	if files[0].Path != "main.go" || files[1].Path != "util.go" {
		t.Fatalf("unexpected paths: %q %q", files[0].Path, files[1].Path)
	}
}

func TestAddedRemovedCounts(t *testing.T) {
	files := Parse(sample)
	if got := files[0].Added(); got != 2 {
		t.Errorf("main.go added: want 2, got %d", got)
	}
	if got := files[0].Removed(); got != 1 {
		t.Errorf("main.go removed: want 1, got %d", got)
	}
	if got := files[1].Added(); got != 1 {
		t.Errorf("util.go added: want 1, got %d", got)
	}
}

func TestHunkHeaderPreserved(t *testing.T) {
	files := Parse(sample)
	if len(files[0].Hunks) != 1 || files[0].Hunks[0].Header == "" {
		t.Fatalf("hunk header not captured: %+v", files[0].Hunks)
	}
}

func TestParseEmpty(t *testing.T) {
	if got := Parse(""); len(got) != 0 {
		t.Errorf("empty diff should yield 0 files, got %d", len(got))
	}
}

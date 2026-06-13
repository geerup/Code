// Package gitdiff parses unified-diff output into per-file hunks so the
// reviewer can attach comments to specific files and changed line ranges.
package gitdiff

import (
	"bufio"
	"strings"
)

// FileDiff is the set of changes to a single file.
type FileDiff struct {
	Path  string
	Hunks []Hunk
}

// Hunk is one @@ ... @@ section with its added/removed lines.
type Hunk struct {
	Header string
	Lines  []Line
}

// Line is a single diff line. Kind is '+', '-', or ' ' (context).
type Line struct {
	Kind byte
	Text string
}

// Added reports the number of inserted lines in the file.
func (f FileDiff) Added() int { return f.count('+') }

// Removed reports the number of deleted lines in the file.
func (f FileDiff) Removed() int { return f.count('-') }

func (f FileDiff) count(kind byte) int {
	n := 0
	for _, h := range f.Hunks {
		for _, l := range h.Lines {
			if l.Kind == kind {
				n++
			}
		}
	}
	return n
}

// Parse turns `git diff` unified output into structured FileDiffs.
func Parse(diff string) []FileDiff {
	var files []FileDiff
	var cur *FileDiff
	var hunk *Hunk

	sc := bufio.NewScanner(strings.NewReader(diff))
	sc.Buffer(make([]byte, 1024*1024), 1024*1024)
	for sc.Scan() {
		line := sc.Text()
		switch {
		case strings.HasPrefix(line, "diff --git"):
			if cur != nil {
				if hunk != nil {
					cur.Hunks = append(cur.Hunks, *hunk)
					hunk = nil
				}
				files = append(files, *cur)
			}
			cur = &FileDiff{Path: parsePath(line)}
		case strings.HasPrefix(line, "+++ b/"):
			if cur != nil {
				cur.Path = strings.TrimPrefix(line, "+++ b/")
			}
		case strings.HasPrefix(line, "@@"):
			if cur == nil {
				continue
			}
			if hunk != nil {
				cur.Hunks = append(cur.Hunks, *hunk)
			}
			hunk = &Hunk{Header: line}
		case hunk != nil && len(line) > 0 && (line[0] == '+' || line[0] == '-' || line[0] == ' '):
			if strings.HasPrefix(line, "+++") || strings.HasPrefix(line, "---") {
				continue
			}
			hunk.Lines = append(hunk.Lines, Line{Kind: line[0], Text: line[1:]})
		}
	}
	if cur != nil {
		if hunk != nil {
			cur.Hunks = append(cur.Hunks, *hunk)
		}
		files = append(files, *cur)
	}
	return files
}

func parsePath(diffLine string) string {
	// "diff --git a/foo.go b/foo.go" -> "foo.go"
	fields := strings.Fields(diffLine)
	if len(fields) >= 4 {
		return strings.TrimPrefix(fields[3], "b/")
	}
	return ""
}

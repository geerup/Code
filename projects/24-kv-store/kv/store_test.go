package kv

import (
	"bufio"
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestPutGetDelete(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()

	if err := s.Put("a", []byte("apple")); err != nil {
		t.Fatal(err)
	}
	v, err := s.Get("a")
	if err != nil || !bytes.Equal(v, []byte("apple")) {
		t.Fatalf("get a = %q, %v", v, err)
	}
	if _, err := s.Get("missing"); err != ErrNotFound {
		t.Errorf("want ErrNotFound, got %v", err)
	}
	if err := s.Delete("a"); err != nil {
		t.Fatal(err)
	}
	if _, err := s.Get("a"); err != ErrNotFound {
		t.Errorf("deleted key should be gone, got %v", err)
	}
}

func TestOverwriteKeepsLatest(t *testing.T) {
	s, _ := Open(t.TempDir())
	defer s.Close()
	_ = s.Put("k", []byte("v1"))
	_ = s.Put("k", []byte("v2"))
	v, _ := s.Get("k")
	if string(v) != "v2" {
		t.Errorf("want v2, got %q", v)
	}
}

func TestRecoveryAfterReopen(t *testing.T) {
	dir := t.TempDir()
	s, _ := Open(dir)
	_ = s.Put("name", []byte("ann"))
	_ = s.Put("city", []byte("paris"))
	_ = s.Delete("city")
	_ = s.Close()

	// Reopen: the index must rebuild from the WAL.
	s2, err := Open(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer s2.Close()
	if v, _ := s2.Get("name"); string(v) != "ann" {
		t.Errorf("recovered name = %q, want ann", v)
	}
	if _, err := s2.Get("city"); err != ErrNotFound {
		t.Error("deleted key must stay deleted after recovery")
	}
}

func TestRecoveryIgnoresTornTail(t *testing.T) {
	dir := t.TempDir()
	s, _ := Open(dir)
	_ = s.Put("good", []byte("data"))
	_ = s.Close()

	// Simulate a crash mid-write: append garbage bytes to the log tail.
	f, _ := os.OpenFile(filepath.Join(dir, "data.wal"), os.O_WRONLY|os.O_APPEND, 0o644)
	_, _ = f.Write([]byte{0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x00, 0x00, 0x05})
	_ = f.Close()

	s2, err := Open(dir)
	if err != nil {
		t.Fatalf("store should recover past a torn tail, got %v", err)
	}
	defer s2.Close()
	if v, _ := s2.Get("good"); string(v) != "data" {
		t.Errorf("valid record before torn tail must survive, got %q", v)
	}
}

func TestCompactReclaimsAndPreservesData(t *testing.T) {
	dir := t.TempDir()
	s, _ := Open(dir)
	for i := 0; i < 100; i++ {
		_ = s.Put("k", []byte("value-overwritten-many-times"))
	}
	_ = s.Put("keep", []byte("v"))

	before, _ := os.Stat(filepath.Join(dir, "data.wal"))
	if err := s.Compact(); err != nil {
		t.Fatal(err)
	}
	after, _ := os.Stat(filepath.Join(dir, "data.wal"))
	if after.Size() >= before.Size() {
		t.Errorf("compaction should shrink the log: before=%d after=%d", before.Size(), after.Size())
	}

	// Writes still work post-compaction and data survives a reopen.
	_ = s.Put("post", []byte("compact"))
	_ = s.Close()
	s2, _ := Open(dir)
	defer s2.Close()
	if v, _ := s2.Get("k"); string(v) != "value-overwritten-many-times" {
		t.Errorf("k lost after compact, got %q", v)
	}
	if v, _ := s2.Get("post"); string(v) != "compact" {
		t.Errorf("post-compact write lost, got %q", v)
	}
	if s2.Len() != 3 {
		t.Errorf("want 3 live keys, got %d", s2.Len())
	}
}

func TestChecksumDetectsCorruption(t *testing.T) {
	rec := encode(record{op: opPut, key: []byte("k"), value: []byte("v")})
	rec[len(rec)-1] ^= 0xFF // flip a bit in the value
	r := bufio.NewReader(bytes.NewReader(rec))
	if _, err := readRecord(r); err != ErrCorrupt {
		t.Errorf("want ErrCorrupt, got %v", err)
	}
}

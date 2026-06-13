package kv

import (
	"bufio"
	"errors"
	"os"
	"path/filepath"
	"sync"
)

// ErrNotFound is returned for missing keys.
var ErrNotFound = errors.New("kv: key not found")

// Store is a durable, goroutine-safe key-value store.
type Store struct {
	mu    sync.RWMutex
	dir   string
	file  *os.File
	w     *bufio.Writer
	index map[string][]byte // in-memory copy of live values
}

// Open opens (or creates) a store rooted at dir, replaying the WAL to recover.
func Open(dir string) (*Store, error) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	s := &Store{dir: dir, index: make(map[string][]byte)}
	if err := s.recover(); err != nil {
		return nil, err
	}
	f, err := os.OpenFile(s.logPath(), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return nil, err
	}
	s.file = f
	s.w = bufio.NewWriter(f)
	return s, nil
}

func (s *Store) logPath() string { return filepath.Join(s.dir, "data.wal") }

// recover replays the WAL to rebuild the in-memory index. A corrupt/truncated
// tail (e.g. from a crash mid-write) is treated as the end of the valid log.
func (s *Store) recover() error {
	f, err := os.Open(s.logPath())
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	defer f.Close()

	r := bufio.NewReader(f)
	for {
		rec, err := readRecord(r)
		if err != nil {
			if errors.Is(err, ErrCorrupt) || errors.Is(err, os.ErrDeadlineExceeded) {
				break // stop at the first bad record (torn write)
			}
			break // io.EOF / unexpected EOF → done
		}
		switch rec.op {
		case opPut:
			s.index[string(rec.key)] = append([]byte(nil), rec.value...)
		case opDelete:
			delete(s.index, string(rec.key))
		}
	}
	return nil
}

// Put stores a value durably (append + flush + fsync).
func (s *Store) Put(key string, value []byte) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, err := s.w.Write(encode(record{op: opPut, key: []byte(key), value: value})); err != nil {
		return err
	}
	if err := s.flushSync(); err != nil {
		return err
	}
	s.index[key] = append([]byte(nil), value...)
	return nil
}

// Get returns the value for key, or ErrNotFound.
func (s *Store) Get(key string) ([]byte, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	v, ok := s.index[key]
	if !ok {
		return nil, ErrNotFound
	}
	return append([]byte(nil), v...), nil
}

// Delete writes a tombstone and removes the key.
func (s *Store) Delete(key string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.index[key]; !ok {
		return ErrNotFound
	}
	if _, err := s.w.Write(encode(record{op: opDelete, key: []byte(key)})); err != nil {
		return err
	}
	if err := s.flushSync(); err != nil {
		return err
	}
	delete(s.index, key)
	return nil
}

// Keys returns all live keys (unordered).
func (s *Store) Keys() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	keys := make([]string, 0, len(s.index))
	for k := range s.index {
		keys = append(keys, k)
	}
	return keys
}

// Len returns the number of live keys.
func (s *Store) Len() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.index)
}

func (s *Store) flushSync() error {
	if err := s.w.Flush(); err != nil {
		return err
	}
	return fsync(s.file)
}

// Compact rewrites the log with only live records, reclaiming space taken by
// overwritten/deleted keys. Done atomically via a temp file + rename.
func (s *Store) Compact() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	tmp := s.logPath() + ".compact"
	f, err := os.OpenFile(tmp, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	w := bufio.NewWriter(f)
	for k, v := range s.index {
		if _, err := w.Write(encode(record{op: opPut, key: []byte(k), value: v})); err != nil {
			f.Close()
			return err
		}
	}
	if err := w.Flush(); err != nil {
		f.Close()
		return err
	}
	if err := f.Sync(); err != nil {
		f.Close()
		return err
	}
	f.Close()

	if err := s.file.Close(); err != nil {
		return err
	}
	if err := os.Rename(tmp, s.logPath()); err != nil {
		return err
	}
	nf, err := os.OpenFile(s.logPath(), os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return err
	}
	s.file = nf
	s.w = bufio.NewWriter(nf)
	return nil
}

// Close flushes and closes the underlying file.
func (s *Store) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if err := s.w.Flush(); err != nil {
		return err
	}
	return s.file.Close()
}

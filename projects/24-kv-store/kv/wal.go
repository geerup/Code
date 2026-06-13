// Package kv implements a small persistent key-value store using an
// append-only write-ahead log (WAL) plus an in-memory hash index — the same
// log-structured idea behind Bitcask. Writes append a record and update the
// index; reads hit the index. On open, the log is replayed to rebuild the
// index, giving crash recovery.
package kv

import (
	"bufio"
	"encoding/binary"
	"errors"
	"hash/crc32"
	"io"
	"os"
)

// Record layout on disk (all big-endian):
//
//	crc32 (4) | op (1) | keyLen (4) | valLen (4) | key | value
//
// op: 0 = put, 1 = delete (tombstone, valLen == 0).
const (
	opPut    byte = 0
	opDelete byte = 1

	headerSize = 4 + 1 + 4 + 4
)

var (
	// ErrCorrupt indicates a record failed its checksum (truncated/garbled log).
	ErrCorrupt = errors.New("kv: corrupt record")
	crcTable   = crc32.MakeTable(crc32.Castagnoli)
)

type record struct {
	op    byte
	key   []byte
	value []byte
}

// encode serializes a record with a leading CRC over (op|keyLen|valLen|key|val).
func encode(r record) []byte {
	body := make([]byte, headerSize-4+len(r.key)+len(r.value))
	body[0] = r.op
	binary.BigEndian.PutUint32(body[1:5], uint32(len(r.key)))
	binary.BigEndian.PutUint32(body[5:9], uint32(len(r.value)))
	copy(body[9:], r.key)
	copy(body[9+len(r.key):], r.value)

	out := make([]byte, 4+len(body))
	binary.BigEndian.PutUint32(out[0:4], crc32.Checksum(body, crcTable))
	copy(out[4:], body)
	return out
}

// readRecord reads and verifies one record from r. Returns io.EOF at end.
func readRecord(r *bufio.Reader) (record, error) {
	header := make([]byte, headerSize)
	if _, err := io.ReadFull(r, header); err != nil {
		return record{}, err // io.EOF or io.ErrUnexpectedEOF
	}
	crc := binary.BigEndian.Uint32(header[0:4])
	op := header[4]
	keyLen := binary.BigEndian.Uint32(header[5:9])
	valLen := binary.BigEndian.Uint32(header[9:13])

	payload := make([]byte, keyLen+valLen)
	if _, err := io.ReadFull(r, payload); err != nil {
		return record{}, io.ErrUnexpectedEOF
	}

	body := append(header[4:13:13], payload...)
	if crc32.Checksum(body, crcTable) != crc {
		return record{}, ErrCorrupt
	}
	return record{op: op, key: payload[:keyLen], value: payload[keyLen:]}, nil
}

// fsync flushes a file's contents to stable storage.
func fsync(f *os.File) error { return f.Sync() }

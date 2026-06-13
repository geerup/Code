# 🗄️ Persistent Key-Value Store (#24) ★

A durable, crash-safe key-value store built from scratch in Go — a
**log-structured** store in the style of Bitcask: an append-only **write-ahead
log** for durability plus an in-memory hash index for O(1) reads.

## Guarantees & mechanics
- **Durable writes.** Every `Put`/`Delete` appends a CRC-checksummed record and
  `fsync`s before returning.
- **Crash recovery.** On `Open`, the WAL is replayed to rebuild the index. A
  **torn write** at the tail (partial record from a crash) is detected by its
  checksum and treated as end-of-log, so valid earlier data always survives.
- **Compaction.** `Compact()` rewrites the log with only live records
  (reclaiming space from overwrites/deletes) atomically via temp-file + rename.
- **Concurrency-safe.** `sync.RWMutex` around the index and log.

## Record format
```
crc32c (4) | op (1) | keyLen (4) | valLen (4) | key | value
```

## Tests (`kv/store_test.go`)
put/get/delete · overwrite-keeps-latest · **recovery after reopen** ·
**recovery ignores a torn tail** · **compaction shrinks log & preserves data** ·
**checksum detects corruption**.

## Run
```bash
go test ./...
go run ./cmd/kvserver --dir ./data        # REST: PUT/GET/DELETE /kv/{key}, POST /compact
```

## What I learned / next
- Why WAL + fsync gives durability, how checksums make recovery safe against
  partial writes, and log compaction.
- Next: a hint file to skip full replay, value-only-on-disk index (true Bitcask),
  and a Postgres-style B-tree variant for range scans.

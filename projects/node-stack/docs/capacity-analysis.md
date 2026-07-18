# Capacity analysis: node-stack RAM working set

This is the artifact that stopped a deployment before it became a bad one. The
question: does the concurrent working set of `bitcoind` + `fulcrum` + `monerod` fit in
available RAM on the target host, without falling back to disk-thrashing swap during
sync or indexing?

**This document is a structured skeleton.** The category breakdown, formulas, and
what needs to be measured are filled in. The actual numbers are not — they have to
come from my own hardware and real measurements, not be invented here.

> _To be filled in with measured/derived numbers wherever this marker appears._
> _Not to be trusted against estimates alone — I plan to validate against `free -m` /
> `docker stats` during an actual sync before relying on the plan._

## 1. Target hardware

> _To be filled in — total RAM installed, RAM after the planned upgrade, CPU, storage
> type (SSD/NVMe/HDD — matters a lot for bitcoind/Fulcrum I/O patterns if RAM is tight
> and swap gets touched at all)._

| Spec | Current | After upgrade |
|---|---|---|
| Total RAM | _to be measured_ | _to be measured_ |
| Storage | _to be measured_ | — |
| Other concurrent workloads on this host | _to be measured (e.g. homelab compose stack, monitoring-stack)_ | — |

## 2. Working-set components

### 2a. bitcoind

- **UTXO set cache (`dbcache`)**: the primary tunable. Bitcoin Core's default is
  usually 450 MB, but a full node benefits significantly from a larger cache during
  initial sync (fewer disk flushes) — larger values trade RAM for sync speed.
- **Non-cache overhead**: mempool, connection/peer state, indexes if enabled
  (`-txindex=1` adds a meaningful additional index on top of the base chainstate).

> _To be filled in — planned `dbcache` value, measured RSS of the `bitcoind` process
> at that setting (idle, and during a sync if I have that data), whether
> `-txindex` is actually needed for this stack (Fulcrum builds its own index — confirm
> whether bitcoind-level txindex is redundant with Fulcrum's own indexing before
> assuming both are needed)._

| Component | Value |
|---|---|
| Configured `dbcache` | _to be measured_ |
| Measured/estimated bitcoind RSS | _to be measured_ |
| `-txindex` enabled? Why/why not | _to be determined_ |

### 2b. Fulcrum

- Fulcrum maintains its own database (RocksDB-backed) indexing the full UTXO set and
  address/transaction history to serve Electrum protocol queries — this is a separate
  memory consumer from bitcoind's own cache, not shared with it.
- Initial sync (Fulcrum indexing the full chain from bitcoind) is itself a
  memory-and-I/O-intensive one-time operation, distinct from steady-state serving load.

> _To be filled in — Fulcrum's documented/observed memory footprint for the DB cache
> setting I plan to use, and whether I'm sizing for "keep up with bitcoind sync"
> vs. "steady-state serving only" (initial sync is the peak)._

| Component | Value |
|---|---|
| Configured DB memory setting | _to be measured_ |
| Measured/estimated Fulcrum RSS (initial sync peak) | _to be measured_ |
| Measured/estimated Fulcrum RSS (steady state) | _to be measured_ |

### 2c. monerod

- Monero's node has its own working set (blockchain DB cache, mempool) — distinct
  memory profile from Bitcoin Core, needs its own measurement rather than assuming
  parity.

> _To be filled in — measured/documented monerod RSS at whatever DB sync mode
> (fast/safe) I plan to run._

| Component | Value |
|---|---|
| DB sync mode | _to be determined_ |
| Measured/estimated monerod RSS | _to be measured_ |

## 3. Combined working set vs. available RAM

> _To be filled in — the sum of the three components above, plus OS/other-workload
> overhead, compared against total RAM (current and post-upgrade). This is the
> actual conclusion of the analysis — still to be filled in even after the RAM
> upgrade, and re-validated against real measurements once deployed._

| | Current RAM | Post-upgrade RAM |
|---|---|---|
| bitcoind | _to be measured_ | _to be measured_ |
| Fulcrum | _to be measured_ | _to be measured_ |
| monerod | _to be measured_ | _to be measured_ |
| OS + other workloads headroom | _to be measured_ | _to be measured_ |
| **Total working set** | _to be measured_ | _to be measured_ |
| **Fits without swap?** | _to be determined (expected: no — this is the blocker)_ | _to be determined (expected: yes, validate)_ |

## 4. Why this matters / what happens if ignored

Both `bitcoind` and `monerod` initial sync are multi-day, I/O- and bandwidth-heavy
operations. If the combined working set exceeds available RAM:

- The OS starts swapping active pages, which on a sync-in-progress node means
  disk I/O contention on the exact path that's already the sync bottleneck.
- Fulcrum's indexing (which itself races to keep up with bitcoind during initial
  sync) falls further behind, potentially never catching up under sustained memory
  pressure.
- Worst case: OOM killer takes down one of the three services mid-sync, requiring a
  partial or full resync depending on how the chainstate/index was left.

Restarting a multi-day sync because of a memory-sizing mistake is expensive enough
that verifying capacity up front is clearly worth it — this is the entire justification
for treating RAM as the binding constraint and blocking deployment on the upgrade
rather than deploying now and hoping.

## 5. Conclusion

> _To be filled in once the numbers above are populated — restate the binding
> constraint plainly (e.g. "current RAM: X GB; working set: Y GB; upgrade to Z GB
> resolves it with N GB headroom") and confirm the upgrade target is sufficient before
> deployment._

# Capacity analysis: node-stack RAM working set

This is the artifact that stopped a deployment before it became a bad one. The
question: does the concurrent working set of `bitcoind` + `fulcrum` + `monerod` fit in
available RAM on the target host, without falling back to disk-thrashing swap during
sync or indexing?

**This document is a structured skeleton.** The category breakdown, formulas, and
what needs to be measured are filled in. The actual numbers are not — they have to
come from the operator's real hardware and real measurements, not be invented here.

> OPERATOR: fill in your measured/derived numbers wherever this marker appears.
> Do not deploy against estimates alone — validate against `free -m` / `docker stats`
> during an actual sync before trusting the plan.

## 1. Target hardware

> OPERATOR: fill in — total RAM installed, RAM after the planned upgrade, CPU, storage
> type (SSD/NVMe/HDD — matters a lot for bitcoind/Fulcrum I/O patterns if RAM is tight
> and swap gets touched at all).

| Spec | Current | After upgrade |
|---|---|---|
| Total RAM | > OPERATOR: fill in | > OPERATOR: fill in |
| Storage | > OPERATOR: fill in | — |
| Other concurrent workloads on this host | > OPERATOR: fill in (e.g. homelab compose stack, monitoring-stack) | — |

## 2. Working-set components

### 2a. bitcoind

- **UTXO set cache (`dbcache`)**: the primary tunable. Bitcoin Core's default is
  usually 450 MB, but a full node benefits significantly from a larger cache during
  initial sync (fewer disk flushes) — larger values trade RAM for sync speed.
- **Non-cache overhead**: mempool, connection/peer state, indexes if enabled
  (`-txindex=1` adds a meaningful additional index on top of the base chainstate).

> OPERATOR: fill in — planned `dbcache` value, measured RSS of the `bitcoind` process
> at that setting (idle, and during a sync if you have that data), whether
> `-txindex` is actually needed for this stack (Fulcrum builds its own index — confirm
> whether bitcoind-level txindex is redundant with Fulcrum's own indexing before
> assuming you need both).

| Component | Value |
|---|---|
| Configured `dbcache` | > OPERATOR: fill in |
| Measured/estimated bitcoind RSS | > OPERATOR: fill in |
| `-txindex` enabled? Why/why not | > OPERATOR: fill in |

### 2b. Fulcrum

- Fulcrum maintains its own database (RocksDB-backed) indexing the full UTXO set and
  address/transaction history to serve Electrum protocol queries — this is a separate
  memory consumer from bitcoind's own cache, not shared with it.
- Initial sync (Fulcrum indexing the full chain from bitcoind) is itself a
  memory-and-I/O-intensive one-time operation, distinct from steady-state serving load.

> OPERATOR: fill in — Fulcrum's documented/observed memory footprint for the DB cache
> setting you plan to use, and whether you're sizing for "keep up with bitcoind sync"
> vs. "steady-state serving only" (initial sync is the peak).

| Component | Value |
|---|---|
| Configured DB memory setting | > OPERATOR: fill in |
| Measured/estimated Fulcrum RSS (initial sync peak) | > OPERATOR: fill in |
| Measured/estimated Fulcrum RSS (steady state) | > OPERATOR: fill in |

### 2c. monerod

- Monero's node has its own working set (blockchain DB cache, mempool) — distinct
  memory profile from Bitcoin Core, needs its own measurement rather than assuming
  parity.

> OPERATOR: fill in — measured/documented monerod RSS at whatever DB sync mode
  (fast/safe) you plan to run.

| Component | Value |
|---|---|
| DB sync mode | > OPERATOR: fill in |
| Measured/estimated monerod RSS | > OPERATOR: fill in |

## 3. Combined working set vs. available RAM

> OPERATOR: fill in the sum of the three components above, plus OS/other-workload
> overhead, and compare against total RAM (current and post-upgrade). This is the
> actual conclusion of the analysis — do not skip filling this in even after the RAM
> upgrade; re-validate against real measurements once deployed.

| | Current RAM | Post-upgrade RAM |
|---|---|---|
| bitcoind | > OPERATOR: fill in | > OPERATOR: fill in |
| Fulcrum | > OPERATOR: fill in | > OPERATOR: fill in |
| monerod | > OPERATOR: fill in | > OPERATOR: fill in |
| OS + other workloads headroom | > OPERATOR: fill in | > OPERATOR: fill in |
| **Total working set** | > OPERATOR: fill in | > OPERATOR: fill in |
| **Fits without swap?** | > OPERATOR: fill in (expected: no — this is the blocker) | > OPERATOR: fill in (expected: yes, validate) |

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

> OPERATOR: fill in once the numbers above are populated — restate the binding
> constraint plainly (e.g. "current RAM: X GB; working set: Y GB; upgrade to Z GB
> resolves it with N GB headroom") and confirm the upgrade target is sufficient before
> deployment.

# node-stack

Compose stack for self-custody blockchain infrastructure: Bitcoin Core + Fulcrum
(electrum server) + monerod.

**Status: planned (blocked on RAM upgrade)**

## Capacity analysis first — this is the actual deliverable right now

Before touching deployment, I sized the working set of running all three services
concurrently against available RAM. That analysis is the reason this is labeled
*planned* instead of *running*, and it's the artifact worth reading in this repo —
see `docs/capacity-analysis.md` for the full working-set math.

Short version: a full Bitcoin Core node's UTXO set cache, a Fulcrum index database
(which itself indexes the full UTXO/history set for fast Electrum-protocol lookups),
and a monerod node's working set are each individually meaningful memory consumers.
Run concurrently on the current hardware, the combined working set does not fit
comfortably in available RAM without forcing either aggressive cache-size reductions
(which tank sync/indexing performance and risk swap-induced I/O thrashing on the
underlying storage) or accepting degraded performance that isn't representative of
what this stack is supposed to demonstrate. Deploying anyway and documenting a
thrashing, swap-bound node would produce a worse portfolio artifact than admitting the
constraint and fixing it first.

## Decision + rationale: don't deploy on undersized RAM

The obvious move once the compose file was ready would have been to just run it on the
current hardware and call it done. I didn't, on purpose: an electrum server and two
full nodes fighting each other (and the OS) for page cache on a RAM-constrained host
produces exactly the failure mode that matters most for a crypto-infra role — silent
performance degradation that looks like it's "running" but is actually one large reorg
or index rebuild away from falling over. The capacity analysis in this repo is what
caught that *before* wasting a sync (bitcoind and monerod initial sync are both
multi-day, bandwidth- and I/O-heavy operations — restarting one because it OOM'd or got
swap-thrashed mid-sync is expensive to redo). Doing the math up front and stopping is
the same judgment call that matters in the actual job: not deploying something you
already know can't hold up.

## Current state / next step

- Compose skeleton and `.env.example` are drafted below — service definitions and
  every credential is a placeholder.
- Capacity analysis skeleton is in `docs/capacity-analysis.md`, with the working-set
  math structured but **not yet filled in** — the real memory figures come from
  measuring the actual `dbcache`, Fulcrum DB size, and monerod resident set on real
  synced instances (or from vendor-documented minimums), which I haven't measured on
  target hardware yet.
- **Next step:** complete the RAM upgrade identified as the binding constraint, fill in
  the measured/derived numbers in the capacity analysis, then deploy and swap this
  README's status line to `running`.

## Stack

| Component | Role |
|---|---|
| `bitcoind` | Bitcoin Core full node — validates chain, serves RPC, backs Fulcrum |
| `fulcrum` | Electrum protocol server — indexes the UTXO set/history for wallet queries |
| `monerod` | Monero full node — validates chain, serves RPC |

## Layout

```
node-stack/
├── README.md
├── LICENSE
├── .gitignore
├── compose/
│   └── node-stack.yml       # all creds as env placeholders
├── docs/
│   └── capacity-analysis.md # working-set math skeleton, numbers pending
└── .env.example              # placeholder RPC creds only
```

## Deploy (once unblocked)

```bash
cp .env.example .env            # fill in real values in .env, never commit it
docker compose -f compose/node-stack.yml up -d
```

Every credential and path in this repo is a placeholder. Nothing here has synced
against mainnet or holds real wallet material.

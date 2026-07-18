# headscale-stack

Self-hosted WireGuard mesh coordination server: Headscale (control plane) + Headplane
(web UI) + Caddy (reverse proxy / TLS termination), replacing a vendor-run coordination
server with one I run myself.

**Status: planned / evaluated (not yet deployed)**

## What this is

Overlay mesh VPNs (Tailscale-style WireGuard mesh) need a coordination server to hand
out node keys, exchange public keys between peers, and enforce ACLs — the actual
encrypted tunnels are peer-to-peer, but someone has to introduce the peers. Tailscale's
own coordination server is fine functionally, but it means every device I own trusts a
third party to keep issuing valid keys and to keep its ACL/DNS control plane available.

Headscale is an open-source, self-hosted reimplementation of that coordination server
that speaks the same client protocol as Tailscale. Headplane adds a web UI on top
(Headscale itself is API/CLI-only). Caddy sits in front for automatic TLS and to be
the single exposed port.

This repo is the compose stack and reverse-proxy config for standing that up. It is
**not deployed yet** — see "Current state / next step" below.

## Current state / next step

- Evaluated Headscale as the replacement control plane; picked it over the alternatives
  below (see `docs/why-self-host-control-plane.md`).
- Compose skeleton and Caddy config are drafted in this repo as templates — domains,
  keys, and node data are all placeholders.
- **Not yet deployed.** Next step: provision a small always-on host (or reuse existing
  homelab capacity) with a public DNS name pointed at it, deploy the compose stack,
  point Caddy at real DNS with Let's Encrypt, then migrate homelab nodes off the
  existing overlay one at a time (keep the old coordination server reachable until every
  node has re-registered against Headscale, so nothing gets stranded mid-migration).
- Once live: swap the README status line to `running`, drop in the real (still
  redacted) ACL policy, and record actual node counts / uptime.

## Decision + rationale: Headscale over ZeroTier

I looked at ZeroTier as an alternative before settling on Headscale/Tailscale-protocol.
The deciding factor wasn't feature parity — both handle NAT traversal and mesh
membership fine — it was **control-plane licensing risk**. ZeroTier relicensed its
controller (`ztncui`/central controller components) away from a fully open model,
which means a self-hosted ZeroTier controller I stand up today could face licensing
terms tomorrow that I don't control and didn't agree to at deploy time. That's an
unacceptable dependency for infrastructure that's supposed to be removing a
third-party trust point, not creating a new one under a different name.

Headscale is AGPL and reimplements the (documented, stable) Tailscale coordination
protocol independently — it isn't a fork of vendor code subject to the vendor's
relicensing decisions. The tradeoff: Headscale doesn't have Tailscale's polish (no
first-party admin UI, some newer features lag), which is why Headplane is in this
stack — it's the missing UI layer. I'm trading a small amount of feature currency for
not having my mesh's control plane depend on a single company's licensing choices.

## Why self-host the control plane at all

See `docs/why-self-host-control-plane.md` for the full writeup — short version: the
tunnels are already peer-to-peer WireGuard, so the only thing a vendor coordination
server buys me over a self-hosted one is convenience. Removing it removes the last
third-party dependency in the homelab's networking stack (see `homelab` repo — the
overlay-only bind pattern already assumes a WireGuard mesh; this decides who runs its
coordination server).

## Stack

| Component | Role |
|---|---|
| `headscale` | Coordination server — node registration, key exchange, ACLs, DNS |
| `headplane` | Web UI for Headscale (Headscale itself has no bundled UI) |
| `caddy` | Reverse proxy, automatic TLS, single exposed port |

## Layout

```
headscale-stack/
├── README.md
├── LICENSE
├── .gitignore
├── compose/
│   └── headscale.yml        # Headscale + Headplane, placeholder domain/keys
├── caddy/
│   └── Caddyfile.example    # reverse-proxy template, placeholder domain
└── docs/
    └── why-self-host-control-plane.md
```

## Deploy (once unblocked)

```bash
cp compose/headscale.yml compose/headscale.local.yml   # fill in real domain/config
cp caddy/Caddyfile.example caddy/Caddyfile              # fill in real domain
# generate a Headscale pre-auth key per node at registration time — never commit one
docker compose -f compose/headscale.local.yml up -d
```

All domains and keys in this repo are placeholders. Nothing here has been run against
real infrastructure yet.

# homelab

A Docker-composed self-hosted service stack running on a Mele N100 mini PC, where every
service is bound only to a WireGuard overlay address and nothing is exposed to the public
internet. It solves the usual self-hosting problem — how to reach your own services
remotely without opening ports to the world — by making overlay membership, not port
forwarding, the sole path in.

Status: running (the compose files here are sanitized templates — placeholders for bind addresses, domains, and tokens)

The compose files in `compose/` are sanitized templates carrying placeholders
(`${OVERLAY_BIND_ADDR}`, `${*_TOKEN}`, etc.). Supply your own bind address, domains, and
tokens through `.env` to run them. Each file carries a `# Sanitized template` header as a
reminder that the values are placeholders.

## Architecture

Every service publishes its port to `${OVERLAY_BIND_ADDR}` — the host's address on the
WireGuard/Tailscale overlay interface — and never to `0.0.0.0`. The home router has no
port forwards to any of these services. See [`docs/architecture.md`](docs/architecture.md)
for the network diagram and how to verify the bind on the host.

### The key decision: overlay-only bind, no port forwards

The obvious way to reach a self-hosted service remotely is to forward a port on the router
and put a reverse proxy with auth in front of it. That publishes a listener on the public
internet and makes the service's security depend on that auth never having a bug, plus
constant patching of an internet-facing surface.

This stack does the opposite. Docker's default `-p 8080:8080` binds to all interfaces
(`0.0.0.0`); here every mapping is prefixed with the host's overlay address
(`${OVERLAY_BIND_ADDR}:8080:8080`), so the listener exists only on the overlay NIC. Access
control becomes membership in the overlay, enforced by the coordination server before any
packet reaches a service. The result is zero public attack surface: an internet scanner
finds no open ports for these services, because there is no `0.0.0.0` listener and no
forward to reach one. Per-service auth (Vaultwarden, code-server, Dozzle) still runs as
defense in depth, but it is the inner boundary, not the only one.

## Services

| Service      | Purpose                                  | Container port | Overlay port (via `.env`)   |
|--------------|------------------------------------------|----------------|-----------------------------|
| forgejo      | Self-hosted Git forge                    | 3000 / 22      | `FORGEJO_HTTP_PORT` / `FORGEJO_SSH_PORT` |
| act-runner   | CI executor (pulls jobs from Forgejo)    | none (outbound)| none — no inbound listener  |
| vaultwarden  | Bitwarden-compatible secrets manager     | 80             | `VAULTWARDEN_HTTP_PORT`     |
| code-server  | VS Code in the browser                   | 8080           | `CODE_SERVER_HTTP_PORT`     |
| dozzle       | Real-time Docker log viewer              | 8080           | `DOZZLE_HTTP_PORT`          |
| uptime-kuma  | Status / uptime monitoring dashboard     | 3001           | `UPTIME_KUMA_HTTP_PORT`     |

## Deploy

Prerequisites:

- A Linux host with Docker Engine and the Compose plugin.
- The host joined to a WireGuard overlay (Tailscale today; Headscale planned). Know the
  host's overlay-interface address — that is `OVERLAY_BIND_ADDR`.
- No router port forwards to these services.

Steps:

```bash
cp .env.example .env
# Edit .env: set OVERLAY_BIND_ADDR to the host's overlay address, set ports,
# and fill in every secret (tokens, passwords). Never commit .env.

# Bring services up individually (each service is its own compose file):
docker compose -f compose/forgejo.yml up -d
docker compose -f compose/act-runner.yml up -d      # after Forgejo is registered
docker compose -f compose/vaultwarden.yml up -d
docker compose -f compose/code-server.yml up -d
docker compose -f compose/dozzle.yml up -d
docker compose -f compose/uptime-kuma.yml up -d
```

The services are split into per-service compose files rather than one file so each can be
started, stopped, and updated independently. act-runner has no `depends_on` on Forgejo
because they live in separate files: start Forgejo first, mint a runner registration token
in its admin UI, put it in `.env` as `ACT_RUNNER_TOKEN`, then start the runner.

Verify the bind after `up`:

```bash
sudo ss -tlnp        # every listener should show OVERLAY_BIND_ADDR, never 0.0.0.0
```

## Networking model

Connectivity is a WireGuard mesh. Today the coordination server is **Tailscale**, with
**MagicDNS** giving each host a stable name so services are reached by name over the
overlay rather than by raw address. Devices that are not overlay members have no route to
any service.

The direction of travel is toward **Headscale** — a self-hosted, open-source
implementation of the Tailscale coordination server — to remove the dependency on a
third-party control plane while keeping the same client and the same overlay-only bind
model. That work is tracked separately (see the `headscale-stack` repo) and does not
change the pattern here: services still bind to the overlay address only.

## Security posture

- **No public exposure.** Overlay-only bind (`${OVERLAY_BIND_ADDR}`, never `0.0.0.0`) plus
  no router port forwards. The public attack surface for this stack is zero.
- **Secrets stay out of the repo.** All credentials, tokens, real overlay addresses, and
  domains come from `.env` (git-ignored). `.env.example` holds placeholders only; the
  compose files reference variables, never literal secrets.
- **Defense in depth.** Vaultwarden `ADMIN_TOKEN`, code-server `PASSWORD`, and Dozzle
  simple-auth remain enabled so a compromised overlay member still meets per-service auth.
- **Least privilege on the Docker socket.** Dozzle mounts the socket read-only; act-runner
  needs it read-write to spawn job containers, which is an accepted trade-off documented in
  its compose file.
- **Signups closed.** Vaultwarden `SIGNUPS_ALLOWED=false`; new users are invited from the
  admin panel over the overlay.

The compose files ship as sanitized templates; `docs/architecture.md` lists the checks I
run on the host to confirm every listener is overlay-only and nothing is forwarded.

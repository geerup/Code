# Architecture — overlay-only bind pattern

Every service in this stack publishes its port **only** to the host's address on the
WireGuard/Tailscale overlay interface (`${OVERLAY_BIND_ADDR}`). Nothing is bound to
`0.0.0.0`, and the router has **no port forwards** to any of these services. The only
way to reach them is to be a member of the overlay (tailnet). The internet-facing
attack surface for this stack is therefore zero: an unauthenticated scanner on the WAN
sees no open ports for these services at all.

## Network diagram

```mermaid
flowchart LR
    subgraph clients["Overlay members (authenticated devices)"]
        laptop["Laptop"]
        phone["Phone"]
    end

    subgraph overlay["Encrypted overlay (WireGuard via Tailscale/MagicDNS)"]
        direction TB
        coord["Coordination server\n(Tailscale today -> Headscale planned)"]
    end

    wan(["Public internet\n(no port forwards)"])

    subgraph host["Mele N100 host"]
        direction TB
        bind["Overlay iface bind\n${OVERLAY_BIND_ADDR} only"]
        subgraph svcs["Docker services"]
            forgejo["forgejo :3000 / ssh"]
            runner["act-runner (outbound only,\nno listening port)"]
            vault["vaultwarden :80"]
            code["code-server :8080"]
            dozzle["dozzle :8080"]
            kuma["uptime-kuma :3001"]
        end
    end

    laptop -- WireGuard --> overlay
    phone -- WireGuard --> overlay
    overlay --> bind
    bind --> forgejo
    bind --> vault
    bind --> code
    bind --> dozzle
    bind --> kuma
    runner -- pulls jobs over overlay --> forgejo
    wan -. blocked: no forward, no 0.0.0.0 bind .-> host
```

## Why this shape

- **Bind to the overlay address, not `0.0.0.0`.** Docker's default `-p 8080:8080`
  binds to all interfaces. Prefixing the host address (`${OVERLAY_BIND_ADDR}:8080:8080`)
  restricts the listener to the overlay NIC. Even if the router later gains an accidental
  forward, there is no `0.0.0.0` listener to reach.
- **No port forwards.** Access control is membership in the overlay, enforced by the
  coordination server, not by exposing ports and layering auth on top.
- **act-runner has no inbound port.** It dials out to Forgejo over the overlay and pulls
  jobs. It only mounts the Docker socket to spawn job containers locally.
- **Defense in depth still applies.** Vaultwarden, code-server, and Dozzle each keep
  their own auth enabled; the overlay is the outer boundary, not the only one.

---

## Verifying the bind on the host

These are the checks I run on the host to confirm the overlay-only pattern actually holds.
The compose files ship as sanitized templates, so the addresses and ports here are
placeholders until set in `.env`:

- [ ] `OVERLAY_BIND_ADDR` is the host's actual overlay-interface address (not LAN, not
      `0.0.0.0`, not loopback).
- [ ] `sudo ss -tlnp` shows every service listening only on the overlay address, never
      `0.0.0.0` / `*`.
- [ ] Router/firewall has **no** port forwards to the host for any of these ports.
- [ ] `nmap` from an off-overlay host shows these ports filtered/closed.
- [ ] Ports in the diagram match the real published ports (`.env` values).
- [ ] Coordination server reality: Tailscale vs. Headscale — the diagram label matches.
- [ ] act-runner truly exposes no inbound port (`docker ps` shows no published ports).
- [ ] No real overlay addresses, MagicDNS names, domains, or tokens remain in any file.

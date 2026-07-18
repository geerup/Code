# Why self-host the WireGuard control plane

## The problem this solves

A mesh WireGuard overlay (Tailscale, Headscale-compatible clients, etc.) forms
peer-to-peer encrypted tunnels between nodes — the coordination server is not in the
data path for actual traffic. Its job is narrower than it looks:

- Issue and revoke node identities (keys) on join/leave.
- Exchange public keys and current endpoints between peers ("who is on the mesh and
  how do I reach them right now").
- Serve/enforce the ACL policy (which nodes can talk to which).
- Optionally serve MagicDNS-style name resolution for the mesh.

Using a vendor-run coordination server (e.g. Tailscale's own) means every device on
the mesh has a hard runtime dependency on that vendor's availability and continued
willingness to serve the account — plus every ACL/DNS decision lives in their control
plane, not mine. For a homelab that's explicitly built around a zero-public-exposure,
overlay-only bind pattern (see the `homelab` repo), the coordination server is the one
piece of the networking stack that *isn't* self-hosted. This project closes that gap.

## What "vendor coordination-server dependency" actually costs

- **Availability risk**: if the vendor's control plane has an outage, new devices
  can't join and existing devices may fail to re-key/re-resolve endpoints on network
  changes, even though the underlying tunnels would otherwise work fine.
- **Policy risk**: ACLs, tagging, and DNS are configured through the vendor's UI/API
  and stored on their infrastructure — not something I can audit, version-control, or
  restore from my own backups without their cooperation.
- **Account risk**: mesh membership is tied to a vendor account/auth flow. Losing
  access to that account (suspension, billing issue, policy change) is losing control
  of the mesh's control plane, not just a inconvenience.
- **Trust surface**: the vendor sees which of my devices exist, when they're online,
  and (depending on config) key metadata — for a homelab built around minimizing what
  third parties can observe, that's a gap worth closing.

None of these are catastrophic on their own. Together they're the reason this is
listed as "evaluated" rather than dismissed — self-hosting the control plane is a
real, deliberate infrastructure decision, not a knee-jerk vendor-avoidance move.

## Alternatives considered

| Option | Verdict |
|---|---|
| Stay on vendor coordination server | Works fine functionally; keeps the dependency this project is meant to remove. |
| ZeroTier (self-hosted controller) | Rejected — see licensing-risk section below. |
| Headscale + Headplane + Caddy | Chosen. AGPL, protocol-compatible with existing clients, active upstream. |
| Nebula (Slack's mesh VPN) | Considered briefly; different trust model (lighthouse + cert-based, not drop-in compatible with existing Tailscale-protocol clients already deployed), would mean re-provisioning every node's client instead of just repointing them at a new coordination server. Not chosen for this round. |

## The licensing-risk angle: Headscale vs. ZeroTier

ZeroTier was the other realistic self-hosted option — it does mesh networking with
NAT traversal and has its own self-hostable controller (`ztncui` and related central
controller tooling). The reason it's not the pick here isn't a feature gap, it's
**licensing risk in the control-plane software itself**.

ZeroTier relicensed its central/controller-adjacent components away from a purely
permissive/open model. That matters specifically for a project whose entire point is
removing a dependency on decisions made by a company I don't control: if I stand up a
self-hosted ZeroTier controller today, I'm still exposed to whatever licensing terms
that company sets for that software going forward — I'd be swapping "vendor controls
my coordination server's *availability*" for "vendor controls my coordination server's
*license terms*". That's not actually independence, it's the same risk in a different
shape.

Headscale sidesteps this because it's an independent, AGPL-licensed reimplementation
of the (stable, documented) Tailscale client protocol — it isn't a fork or derivative
of vendor-controlled code, so there's no single company positioned to relicense the
software I'd be depending on. The AGPL also means any modifications to a
publicly-run instance would themselves have to be shared, which is a reasonable
tradeoff for a project I intend to fully control and self-host anyway.

**Cost of this choice**: Headscale is community-maintained and moves slower than
Tailscale's first-party product — no built-in admin UI (hence adding Headplane
separately), and some newer Tailscale client features aren't guaranteed to have
server-side support yet. That's an accepted tradeoff, not an oversight — the decision
is optimizing for control-plane independence over feature currency.

## Open question for deployment

Migration order (see README "Current state / next step") — need to keep the current
coordination path alive until every node has successfully re-registered against
Headscale, so no device gets stranded off-mesh mid-cutover. This is a deployment-time
concern, not a design blocker.

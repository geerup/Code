<!-- OPERATOR: publish as <username>/<username> or org .github profile README -->

# Portfolio

Infrastructure work across homelabs, embedded hardware, and self-hosted services —
NOC / Linux sysadmin / DevOps / SOC / datacenter roles.

## Systems

- [dotfiles](dotfiles) — Baseline shell/tmux configuration for resilient remote sessions.
- [ansible-homelab](ansible-homelab) — Ansible playbooks that rebuild the homelab stack from a fresh OS.
- [monitoring-stack](monitoring-stack) — Prometheus + Grafana + node_exporter + smartctl_exporter observability stack.
- [backup-restic](backup-restic) — restic backups via systemd timers with a tested restore runbook.
- [kiwix-guide](kiwix-guide) — Offline knowledge infrastructure serving full Wikipedia locally via Kiwix.

## Networking

- [headscale-stack](headscale-stack) — Self-hosted WireGuard coordination server (Headscale + Caddy + Headplane), replacing the vendor control plane.

## Containers

- [homelab](homelab) — Docker-composed self-hosted service stack bound only to a WireGuard overlay, no public exposure.

## Security

- [tor-rotate](tor-rotate) — Tor circuit rotation helpers with NEWNYM rate limiting, plus a SOCKS5 DNS-leak writeup and fix.
- [packet-analysis](packet-analysis) — Annotated pcap analysis demonstrating the SOCKS5 DNS leak and validating the fix.
- [node-stack](node-stack) — Capacity planning and compose design for a Bitcoin Core + Fulcrum + monerod self-custody node stack.

## Hardware

- [uconsole](uconsole) — Build log and operations guide for a heavily-modified uConsole CM4 portable Linux device.

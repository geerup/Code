# Infrastructure Portfolio

A collection of infrastructure projects spanning self-hosted services, configuration
management, observability, backups, network security, and embedded Linux hardware.
Each project lives in its own directory under [`projects/`](projects) with its own
README, real configuration, and an honest status label.

The work targets NOC, Linux sysadmin, DevOps, SRE, SOC, and datacenter roles. The
theme running through it is a zero-public-exposure, self-hosted design: services reachable
only over a WireGuard overlay, secrets kept off the machine, and every deployment
reproducible from files in version control.

> **Honesty note:** projects are labeled by maturity. Some are complete and runnable
> today; some are working scaffolds awaiting import of device-specific source material;
> a few document work that is evaluated but not yet deployed (blocked on hardware). The
> label on each project says which — nothing here is dressed up as more finished than it is.

---

## Projects by domain

### Containers & self-hosting
| Project | What it demonstrates | Status |
|---|---|---|
| [homelab](projects/homelab) | Docker-composed service stack (Forgejo, act_runner CI, Vaultwarden, code-server, Dozzle, Uptime Kuma) bound only to a WireGuard overlay — no public port exposure. | Running; sanitized config import in progress |
| [ansible-homelab](projects/ansible-homelab) | Idempotent, role-structured Ansible that rebuilds the stack from a fresh OS: base hardening, Docker engine, overlay bring-up, service convergence. | Complete |

### Observability & operations
| Project | What it demonstrates | Status |
|---|---|---|
| [monitoring-stack](projects/monitoring-stack) | Prometheus + Grafana + node_exporter + smartctl_exporter, with a scrape design and SMART disk-health monitoring. | Complete (dashboards/screenshots to add) |
| [backup-restic](projects/backup-restic) | restic backups driven by systemd timers, with retention/prune policy and a documented restore runbook. | Complete (restore test to be run & dated) |

### Networking & overlay
| Project | What it demonstrates | Status |
|---|---|---|
| [headscale-stack](projects/headscale-stack) | Self-hosted WireGuard coordination server (Headscale + Caddy + Headplane) evaluated to replace the vendor control plane, including the licensing rationale. | Planned / evaluated |

### Security & network analysis
| Project | What it demonstrates | Status |
|---|---|---|
| [tor-rotate](projects/tor-rotate) | Tor circuit-rotation helpers with NEWNYM rate limiting, plus a writeup of the SOCKS5 DNS-leak footgun and its fix. | Complete |
| [packet-analysis](projects/packet-analysis) | Method and annotated analysis demonstrating the SOCKS5 DNS leak on the wire and validating the fix (tshark/Wireshark). | Writeup complete; captures pending |
| [node-stack](projects/node-stack) | Capacity planning and compose design for a Bitcoin Core + Fulcrum + monerod self-custody stack; identifies RAM as the binding constraint before deployment. | Planned (blocked on RAM) |

### Hardware & embedded Linux
| Project | What it demonstrates | Status |
|---|---|---|
| [uconsole](projects/uconsole) | Build log and operations guide for a heavily-modified uConsole CM4 portable device: EEPROM boot order, NVMe boot, RF/antenna work, power profiling, USB enumeration root-cause. | Device is real; docs being imported |

### Baseline
| Project | What it demonstrates | Status |
|---|---|---|
| [dotfiles](projects/dotfiles) | Shell/tmux configuration for resilient remote sessions over unreliable links. | Structure ready; configs to import |
| [kiwix-guide](projects/kiwix-guide) | Offline knowledge infrastructure — a themed front-end for a local Kiwix server hosting full Wikipedia from NVMe. | Setup docs ready; front-end to import |

---

## Design principles across the portfolio

- **Zero public exposure.** Services bind to a WireGuard overlay address, never `0.0.0.0`. No inbound port forwards.
- **Reproducible from source.** Configuration lives in version control; hosts are rebuildable rather than hand-tuned.
- **Secrets never committed.** Every project ships `.env.example` placeholders and a `.gitignore` that blocks wallet material, RPC credentials, keys, and overlay identifiers. Real values stay on the machine.
- **Honest maturity.** Planned or evaluated work is labeled as such, with a "current state / next step" so nothing reads as vaporware.

## Repository layout

```
projects/
  <project>/
    README.md      # what it is, the key decision + rationale, how to run it
    LICENSE        # MIT
    .gitignore     # tool-appropriate + secret patterns
    ...            # real config, scripts, compose files, docs
```

## License

MIT — see [LICENSE](LICENSE). Set your name in the copyright line before publishing.

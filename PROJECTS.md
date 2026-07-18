# PROJECTS.md — Portfolio Catalog (Source of Truth)

This is the list of repositories to build. The agent (`CLAUDE.md`) reads this to know
what each repo is, where its source material lives, what it should contain, and how it
ties back to résumé bullets and interview prep.

## Status legend

| Code        | Meaning                                                                 |
|-------------|-------------------------------------------------------------------------|
| `PUBLISH`   | Real, working work already exists. Import, sanitize, document, post.     |
| `BUILD`     | Gap-filler. Doesn't exist yet — build it, then it's real and postable.   |
| `BLOCKED`   | Real intent, blocked on hardware/resource. Scaffold + label as planned.  |

**Honesty rule:** a repo's README status line must match reality. `PUBLISH` → "running".
`BUILD` in progress → "in progress". `BLOCKED` → "planned / evaluated". Interviewers
probe these; the real state is strong enough without inflation.

## Owner / naming

Set the GitHub owner in Phase 0 (personal account or `san-media-tech` org). All repo
names below are lowercase, hyphenated. Prefix with the owner at creation time.

## Global sanitization rules

Apply to every repo. See `CLAUDE.md` for the scan. In short: no wallet material, no RPC
creds, no `.env` with real values, no tailnet `100.x` addresses / MagicDNS names / auth
keys, no private keys, no MACs. Replace with placeholders + `.env.example`.

---

# THE REPOS

## 1. `homelab`  — status: PUBLISH  ⭐ start here
**What:** Docker-composed self-hosted service stack, every service bound only to the
WireGuard overlay (no public exposure).
**Target roles:** Linux sysadmin, DevOps, NOC.
**Source:** Mele N100 homelab — the running compose files, `.env` (sanitize hard).
**Structure:**
```
homelab/
├── README.md
├── compose/
│   ├── forgejo.yml         # git forge
│   ├── act-runner.yml      # CI executor
│   ├── vaultwarden.yml     # secrets manager
│   ├── code-server.yml
│   ├── dozzle.yml          # log viewer
│   └── uptime-kuma.yml
├── .env.example            # every var referenced, placeholder values
└── docs/architecture.md    # + a network diagram (Mermaid or exported PNG)
```
**README sections:** Overview → Architecture (overlay-only bind pattern, why no port
forwards) → Services table (name/purpose/port) → Deploy (compose up, prerequisites) →
Networking model (Tailscale/MagicDNS, moving toward Headscale) → Security posture.
**Sanitize:** Vaultwarden data, all real env values, tailnet names, any real domains,
admin tokens, `act_runner` registration token.
**Résumé bullets it backs:** "Deployed and maintained Dockerized self-hosted services…";
"Designed zero-public-exposure service architecture…"; "Built an entire CI/CD pipeline
(Forgejo + act_runner)".
**Interview story:** #5 (self-hosted CI/CD) and #6 (zero public attack surface).

## 2. `uconsole`  — status: PUBLISH  ⭐
**What:** Build log + operations guide for a heavily-modified uConsole CM4 portable Linux
device: AIO v2 upgrade, NVMe boot, RF/antenna work, power profiling, offline stack.
**Target roles:** Datacenter tech, embedded/hardware-adjacent sysadmin.
**Source:** the two markdown setup guides (`/mnt/user-data/outputs/*.md`),
`~/Desktop/uConsole_Setup_Reference.txt`.
**Structure:**
```
uconsole/
├── README.md
├── docs/
│   ├── setup-guide.md          # the living guide(s), merged/cleaned
│   ├── hardware-mods.md        # AIO v2, CM4 adapter, NVMe board, 7-antenna mount
│   ├── boot-and-storage.md     # EEPROM BOOT_ORDER=0xf41 (SD-first, NVMe fallback)
│   ├── power-profiling.md      # idle ~2.75–3W table + method
│   └── ac1200-debug.md         # the enumeration root-cause writeup (see story #1)
└── (optional) config/          # sanitized device-tree params, e.g. dtparam=ant2
```
**README sections:** Overview (what the device is, why) → Hardware config → Boot/storage
rationale → Power results → Notable debugging (link ac1200-debug) → Offline capability.
**Sanitize:** any WiFi creds, real SSIDs, tailnet references in configs.
**Résumé bullets:** "Configured CM4 EEPROM boot order…"; "Performed power consumption
profiling…"; "Configured and tuned 802.11 interfaces…"; "Root-caused USB enumeration
failure…".
**Interview story:** #1 (WiFi enumeration root cause).

## 3. `tor-rotate`  — status: PUBLISH (partial BUILD)
**What:** Tor circuit rotation helpers with NEWNYM rate limiting, plus a writeup of the
SOCKS5 DNS-leak footgun and the fix.
**Target roles:** SOC analyst, Linux sysadmin.
**Source:** the `rotaton` / `rotatoff` shell functions (per notes, not yet persisted to
`.bashrc` — finish them into a proper script as part of this repo).
**Structure:**
```
tor-rotate/
├── README.md
├── tor-rotate.sh           # rotaton/rotatoff as functions or a small CLI
├── docs/
│   ├── newnym-rate-limit.md   # why signals <~10s get coalesced by Tor
│   └── socks5-dns-leak.md     # --socks5 vs --socks5-hostname / torsocks
└── examples/                  # sample torrc snippet (control port config)
```
**README sections:** Problem (metadata leakage) → What this does → NEWNYM rate-limit
explanation → The DNS-leak gotcha (the headline insight) → Usage.
**Sanitize:** control-port password/cookie, any real onion addresses.
**Résumé bullets:** "Identified and remediated DNS leak vector in SOCKS5…"; "implemented
Tor circuit rotation automation with rate limiting".
**Interview story:** #2 (SOCKS5 DNS leak).

## 4. `dotfiles`  — status: PUBLISH
**What:** Baseline shell/tmux config. Small but expected signal.
**Target roles:** all.
**Source:** `~/.bashrc`, `~/.tmux.conf` (and anything else the operator wants public).
**Structure:** `README.md`, `bashrc`, `tmux.conf`, optional `install.sh` (symlink script).
**README sections:** What's here → Install → Notable choices (e.g. tmux for surviving SSH
disconnects on unreliable links).
**Sanitize:** aliases containing hostnames/IPs/tailnet names, any tokens exported in
bashrc, work-specific paths.
**Résumé bullets:** "Used tmux for resilient long-running remote sessions over unreliable
links".

## 5. `kiwix-guide`  — status: PUBLISH
**What:** The themed offline HTML front-end for a local Kiwix server (offline knowledge
infrastructure).
**Target roles:** sysadmin (nice-to-have / personality), frontend-adjacent.
**Source:** `guide.html`.
**Structure:** `README.md`, `guide.html`, optional `docs/kiwix-setup.md` (kiwix-serve
ARM64 static binary, ZIM management, serving full Wikipedia from NVMe).
**README sections:** What it is → Screenshot → How to point it at kiwix-serve → ZIM notes.
**Sanitize:** hardcoded local IPs/hostnames in the HTML → replace with `localhost` or a
placeholder.
**Résumé bullets:** "Built offline knowledge infrastructure serving full Wikipedia locally
via Kiwix…".

---

## 6. `ansible-homelab`  — status: BUILD  ⭐ highest-value build
**What:** Ansible playbooks that rebuild the Mele stack and uConsole base config from a
fresh OS. Turns "I click around in my homelab" into demonstrable infrastructure-as-code.
**Target roles:** DevOps, sysadmin, SRE track.
**Build outline:**
```
ansible-homelab/
├── README.md
├── inventory.example.ini    # placeholder hosts/groups
├── site.yml
├── roles/
│   ├── base/                # packages, users, hardening, tmux
│   ├── docker/              # engine + compose plugin
│   ├── overlay/             # tailscale/headscale client bring-up
│   └── services/            # deploy the homelab compose stack
└── group_vars/all.example.yml
```
**README sections:** What it provisions → Prereqs → Run (`ansible-playbook -i inventory
site.yml`) → Roles table → Idempotency notes.
**Sanitize:** real inventory (ship `.example` only), vault-encrypt any secrets, never
commit the vault password.
**Résumé bullet it creates:** "Authored Ansible playbooks to provision homelab
infrastructure from bare OS (idempotent, role-structured)."

## 7. `monitoring-stack`  — status: BUILD  ⭐ fills the observability gap
**What:** Prometheus + Grafana + node_exporter + smartctl_exporter on the Mele.
Observability is the single biggest gap for NOC/SRE credibility.
**Target roles:** NOC, SRE, DevOps.
**Build outline:**
```
monitoring-stack/
├── README.md
├── compose/monitoring.yml
├── prometheus/prometheus.yml     # scrape configs (placeholder targets)
├── grafana/dashboards/           # exported JSON
└── docs/screenshots/             # real dashboard screenshots (scrub hostnames)
```
**README sections:** What it monitors → Stack diagram → Deploy → Dashboards (screenshots)
→ Alerts (if any) → What each exporter surfaces (disk SMART health, node metrics).
**Sanitize:** scrape targets (IPs/hostnames), Grafana admin creds, any tokens in
dashboard JSON, hostnames baked into screenshots.
**Résumé bullet it creates:** "Deployed Prometheus/Grafana observability with
node_exporter and SMART disk monitoring; built dashboards for host and storage health."

## 8. `backup-restic`  — status: BUILD  ⭐ every interview asks about backups
**What:** restic backups driven by systemd timers, with a **documented, tested restore**.
**Target roles:** sysadmin, DevOps.
**Build outline:**
```
backup-restic/
├── README.md
├── systemd/
│   ├── restic-backup.service
│   └── restic-backup.timer
├── scripts/backup.sh            # excludes, retention, prune
├── scripts/restore-test.sh
└── docs/restore-runbook.md      # the tested restore procedure
```
**README sections:** What it backs up → Schedule (timers) → Retention/prune policy →
**Restore runbook (tested)** → Repo backend notes.
**Sanitize:** restic repo URL/password, backend creds (B2/S3/etc.), real paths that leak
topology.
**Résumé bullet it creates:** "Implemented automated restic backups via systemd timers
with retention/prune policy and a tested restore runbook."

## 9. `packet-analysis`  — status: BUILD  ⭐ SOC gold
**What:** Wireshark/tshark captures demonstrating the SOCKS5 DNS leak and the fix, with
analysis. Proves you can read pcaps and articulate findings — core SOC screening signal.
**Target roles:** SOC analyst, network engineer.
**Build outline:**
```
packet-analysis/
├── README.md
├── captures/                 # SMALL sanitized pcaps only (leak vs fixed)
├── docs/socks5-dns-leak.md   # annotated walkthrough with packet detail
└── docs/method.md            # how captures were taken (tshark filters used)
```
**README sections:** The finding → How to reproduce → Annotated packets (before: DNS to
ISP resolver in clear; after: resolution inside tunnel) → Takeaway.
**Sanitize:** capture on a lab/loopback setup, not personal browsing. Scrub real
destinations, local IPs, MACs. Keep pcaps tiny.
**Résumé bullet it creates:** "Captured and analyzed traffic to demonstrate a SOCKS5 DNS
leak and validate the fix (tshark, Wireshark)."

## 10. `headscale-stack`  — status: BLOCKED (until deployed)
**What:** Headscale + Caddy + Headplane — self-hosted coordination server replacing the
vendor control plane. Strong differentiator once real.
**Target roles:** DevOps, network engineer, privacy-infra employers.
**When to build:** once the operator stands it up. Until then scaffold the README and
compose skeleton and label **planned/evaluated**; include the licensing-risk rationale
(why Headscale over ZeroTier's controller relicense).
**Build outline:**
```
headscale-stack/
├── README.md                 # status: planned/evaluated until live
├── compose/headscale.yml
├── caddy/Caddyfile.example
└── docs/why-self-host-control-plane.md
```
**Sanitize:** ACL policy with real nodes, preauth keys, domains, Caddy TLS material.
**Résumé bullet (as evaluated → then running):** "Evaluated/deployed a self-hosted
WireGuard control plane (Headscale + Caddy + Headplane) to remove third-party
coordination-server dependency."
**Interview story:** ties to #6 (removing the last third-party piece).

## 11. `node-stack`  — status: BLOCKED (RAM constraint)
**What:** Bitcoin Core + Fulcrum (electrs) + monerod compose for self-custody
infrastructure. Niche but real for crypto/privacy employers.
**Target roles:** crypto-infra / node operator roles, DevOps.
**When to build:** after the RAM upgrade the capacity analysis identified. Until then
scaffold + label **planned**, and write up the capacity analysis itself (that's the
valuable artifact right now — see story #4).
**Build outline:**
```
node-stack/
├── README.md                 # status: planned; leads with the capacity analysis
├── compose/node-stack.yml
├── docs/capacity-analysis.md # RAM as binding constraint, working-set math
└── .env.example              # NEVER real RPC creds or wallet paths
```
**Sanitize — CRITICAL:** never commit `bitcoin.conf`/`monerod.conf` with real
`rpcpassword`/`rpc-login`, never wallet files, never addresses tied to the operator.
**Résumé bullet:** "Performed capacity planning for a blockchain node stack (Bitcoin Core,
Fulcrum, monerod); identified RAM as the binding constraint before deployment."
**Interview story:** #4 (capacity analysis that stopped a doomed deployment).

---

## 12. `profile` (optional) — status: BUILD
**What:** A profile README (`<owner>/.github/profile/README.md` for the org, or
`<username>/<username>` for a personal account) that indexes the portfolio: one line per
repo, grouped by domain (Systems / Networking / Containers / Security / Hardware). Ties
the whole thing together for a recruiter landing on the profile.
**Build last**, after several repos exist so the links resolve.

---

# BUILD PRIORITY ORDER

1. `homelab` — source exists, highest signal, backs the most bullets.
2. `uconsole` — source exists, unique hardware depth.
3. `monitoring-stack` — closes the biggest gap (observability).
4. `ansible-homelab` — turns clicking into IaC; top DevOps signal.
5. `backup-restic` — universal interview topic.
6. `packet-analysis` — SOC differentiator.
7. `tor-rotate`, `dotfiles`, `kiwix-guide` — quick PUBLISH wins, do between the above.
8. `headscale-stack`, `node-stack` — when unblocked.
9. `profile` — last.

# RÉSUMÉ BULLET ↔ REPO MAP (for study sessions)

- Zero-public-exposure architecture → `homelab`, `headscale-stack`
- CI/CD (Forgejo + act_runner) → `homelab`
- EEPROM boot order / power profiling / RF tuning → `uconsole`
- USB enumeration root-cause → `uconsole` (story #1)
- SOCKS5 DNS leak / Tor rotation → `tor-rotate`, `packet-analysis` (story #2)
- Infrastructure-as-code → `ansible-homelab`
- Observability / SMART monitoring → `monitoring-stack`
- Backups with tested restore → `backup-restic`
- Node-stack capacity planning → `node-stack` (story #4)
- Self-hosted control plane / licensing analysis → `headscale-stack`
- Offline knowledge infra → `kiwix-guide`
- Resilient remote sessions (tmux) → `dotfiles`

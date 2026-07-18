# Portfolio Build Status
Owner: TBD (operator sets in Phase 0 — `gh` not available in this remote sandbox)        Updated: 2026-07-18 (all 12 scaffolds complete, verified, awaiting operator review)

Built in a remote Claude Code session: local scaffolds only, staged under `repos/`.
No remote GitHub repos created, nothing published. Operator source files
(uConsole guides, real compose files, .bashrc, tmux.conf, guide.html) were not
available in this environment — repos that need them have marked import points.

| Repo             | Status      | Source                          | Notes                                              |
|------------------|-------------|---------------------------------|----------------------------------------------------|
| homelab          | in-review   | operator compose files (absent) | template compose + README; needs real file import  |
| uconsole         | in-review   | operator guides (absent)        | doc skeletons; needs guide import                  |
| tor-rotate       | in-review   | spec (script built fresh)       | tor-rotate.sh authored per spec                    |
| dotfiles         | in-review   | operator dotfiles (absent)      | structure + install.sh; needs real dotfile import  |
| kiwix-guide      | in-review   | guide.html (absent)             | README + setup docs; needs guide.html import       |
| ansible-homelab  | in-review   | built fresh (BUILD)             | full playbooks/roles authored                      |
| monitoring-stack | in-review   | built fresh (BUILD)             | compose + prometheus config; screenshots pending   |
| backup-restic    | in-review   | built fresh (BUILD)             | scripts + systemd units; restore test pending      |
| packet-analysis  | in-review   | built fresh (BUILD)             | method docs; captures must be taken by operator    |
| headscale-stack  | in-review   | planned (BLOCKED)               | labeled planned/evaluated                          |
| node-stack       | in-review   | planned (BLOCKED)               | labeled planned; capacity-analysis skeleton        |
| profile          | in-review   | built fresh                     | index README                                       |

States: not-started → scaffolding → in-review → published-private → public

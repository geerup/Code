# Portfolio Build Status
Owner: TBD (operator sets in Phase 0 — `gh` not available in this remote sandbox)        Updated: 2026-07-18

Built in a remote Claude Code session: local scaffolds only, staged under `repos/`.
No remote GitHub repos created, nothing published. Operator source files
(uConsole guides, real compose files, .bashrc, tmux.conf, guide.html) were not
available in this environment — repos that need them have marked import points.

| Repo             | Status      | Source                          | Notes                                              |
|------------------|-------------|---------------------------------|----------------------------------------------------|
| homelab          | scaffolding | operator compose files (absent) | template compose + README; needs real file import  |
| uconsole         | scaffolding | operator guides (absent)        | doc skeletons; needs guide import                  |
| tor-rotate       | scaffolding | spec (script built fresh)       | tor-rotate.sh authored per spec                    |
| dotfiles         | scaffolding | operator dotfiles (absent)      | structure + install.sh; needs real dotfile import  |
| kiwix-guide      | scaffolding | guide.html (absent)             | README + setup docs; needs guide.html import       |
| ansible-homelab  | scaffolding | built fresh (BUILD)             | full playbooks/roles authored                      |
| monitoring-stack | scaffolding | built fresh (BUILD)             | compose + prometheus config; screenshots pending   |
| backup-restic    | scaffolding | built fresh (BUILD)             | scripts + systemd units; restore test pending      |
| packet-analysis  | scaffolding | built fresh (BUILD)             | method docs; captures must be taken by operator    |
| headscale-stack  | scaffolding | planned (BLOCKED)               | labeled planned/evaluated                          |
| node-stack       | scaffolding | planned (BLOCKED)               | labeled planned; capacity-analysis skeleton        |
| profile          | scaffolding | built fresh                     | index README                                       |

States: not-started → scaffolding → in-review → published-private → public

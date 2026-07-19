# dotfiles

Baseline shell and terminal-multiplexer configuration used across my Linux systems
(homelab host, uConsole portable, remote jump boxes).

Status: in progress (structure and docs ready; sanitized configs still to be added)

## What's here

- `bashrc` — shell config: prompt, aliases, history behavior, PATH additions.
- `tmux.conf` — tmux config: prefix key, pane/window bindings, status line, sensible
  defaults for long-lived sessions.
- `install.sh` — symlinks these files into `$HOME`, backing up anything already there.

Both `bashrc` and `tmux.conf` currently contain a placeholder note instead of the live
config — see "Adding the real configs" below.

## Install

```bash
git clone <repo-url> ~/dotfiles
cd ~/dotfiles
./install.sh
```

`install.sh` will:

1. Back up any existing `~/.bashrc` / `~/.tmux.conf` to `~/.dotfiles-backup/<timestamp>/`.
2. Symlink `bashrc` → `~/.bashrc` and `tmux.conf` → `~/.tmux.conf`.
3. Print what it did so nothing changes silently.

It does not source or `chsh` anything for you — reload with `source ~/.bashrc` or start
a new shell, and `tmux kill-server` / restart tmux to pick up the new config.

## Notable choices

- **tmux as the default terminal multiplexer, not just for pairing.** Sessions run
  detached on remote hosts (homelab box, uConsole over SSH) so a dropped VPN link,
  closed laptop lid, or a flaky mobile hotspot doesn't kill a long-running job or a
  multi-pane debugging session. Reattaching with `tmux attach` restores exactly where
  the work left off — this matters specifically on unreliable links (cellular tethering,
  hotel wifi) where a bare SSH session would just die.
- **Config kept minimal and portable on purpose.** These dotfiles are meant to work
  identically on a full homelab server and on an ARM64 handheld (uConsole); nothing here
  assumes a specific hostname, network, or desktop environment.

## Adding the real configs

`bashrc` and `tmux.conf` are currently placeholders. To populate them:

1. Copy the real `~/.bashrc` / `~/.tmux.conf` over the placeholder files.
2. Strip anything environment-specific: hostnames, IPs, tailnet/MagicDNS names, API
   tokens or keys exported as environment variables, and work-specific paths.
3. Scan for secrets before committing.

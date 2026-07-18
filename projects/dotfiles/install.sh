#!/usr/bin/env bash
#
# install.sh — symlink this repo's dotfiles into $HOME, backing up anything
# already present.
#
# Usage: ./install.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${HOME}/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

# map: source file in this repo -> target path in $HOME
declare -A LINKS=(
  ["bashrc"]="${HOME}/.bashrc"
  ["tmux.conf"]="${HOME}/.tmux.conf"
)

backup_if_exists() {
  local target="$1"

  if [ -e "$target" ] || [ -L "$target" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "Backing up existing $(basename "$target") -> ${BACKUP_DIR}/"
    mv "$target" "${BACKUP_DIR}/$(basename "$target")"
  fi
}

link_file() {
  local src="$1"
  local target="$2"

  if [ ! -e "$src" ]; then
    echo "Skipping $(basename "$src"): not found in $REPO_DIR" >&2
    return
  fi

  backup_if_exists "$target"

  ln -s "$src" "$target"
  echo "Linked $target -> $src"
}

echo "Installing dotfiles from $REPO_DIR"

for name in "${!LINKS[@]}"; do
  link_file "${REPO_DIR}/${name}" "${LINKS[$name]}"
done

if [ -d "$BACKUP_DIR" ]; then
  echo "Existing files backed up to $BACKUP_DIR"
fi

echo "Done. Reload your shell (source ~/.bashrc) and restart tmux to pick up changes."

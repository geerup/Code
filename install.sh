#!/usr/bin/env bash
# Install uConsole AIO Control into a virtualenv and seed an editable config.
# Tested on ClockworkPi uConsole / Debian trixie.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${AIO_VENV:-$HOME/.venvs/aio}"

echo ">> Creating virtualenv at $VENV"
python3 -m venv "$VENV"

echo ">> Installing uConsole AIO Control"
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install "$HERE"

echo ">> Writing default config (if not present)"
"$VENV/bin/aioctl" --init

cat <<EOF

Done.

Run it with:
    $VENV/bin/aioctl

Optionally add a symlink onto your PATH:
    ln -sf "$VENV/bin/aioctl" "\$HOME/.local/bin/aioctl"

Edit your command set any time:
    \$EDITOR "$("$VENV/bin/aioctl" --config-path)"
EOF

"""Command execution helpers.

Commands come from a trusted, user-owned YAML file, so they are run through the
shell to allow pipes, redirects and env expansion. Two distinct execution
modes are provided:

- :func:`run_capture` for one-shot / status commands: waits, captures output.
- :func:`launch_detached` for long-running apps: starts a new session so the
  child keeps running after the TUI exits, and is not killed by Ctrl-C.
"""

from __future__ import annotations

import asyncio
import os
import shlex
import signal
import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    exit_code: int
    output: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


async def run_capture(cmd: str, timeout: float = 30.0) -> CommandResult:
    """Run ``cmd`` via the shell, capturing combined stdout+stderr."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as exc:  # pragma: no cover - extremely rare
        return CommandResult(127, f"failed to start: {exc}")

    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        _terminate(proc)
        return CommandResult(124, f"timed out after {timeout:g}s", timed_out=True)

    text = (stdout or b"").decode("utf-8", errors="replace").rstrip()
    return CommandResult(proc.returncode if proc.returncode is not None else -1, text)


def _terminate(proc: asyncio.subprocess.Process) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


def launch_detached(cmd: str, log_path: str | None = None) -> subprocess.Popen:
    """Launch a long-running program detached from the TUI.

    Output is redirected to ``log_path`` (or discarded) so it does not corrupt
    the terminal UI. The child runs in its own session and survives TUI exit.
    """
    if log_path:
        out = open(log_path, "ab", buffering=0)  # noqa: SIM115 - lifetime tied to child
    else:
        out = subprocess.DEVNULL
    return subprocess.Popen(
        cmd,
        shell=True,
        stdout=out,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


def first_token(cmd: str) -> str:
    """Best-effort program name from a shell command (for pgrep fallback)."""
    try:
        parts = shlex.split(cmd)
    except ValueError:
        parts = cmd.split()
    for part in parts:
        if "=" in part and not part.startswith("/"):
            # skip leading VAR=value assignments
            continue
        return os.path.basename(part)
    return cmd

"""Typed data model for the AIO control config.

Everything the TUI renders is built from these dataclasses, which are in turn
produced from the YAML config by :mod:`aio_control.config`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EntryType(str, Enum):
    """How an entry behaves when activated.

    - ``command``: run once, capture output, show it in the log pane. No
      persistent state.
    - ``app``: launch a long-running / GUI program detached from the TUI.
      Status reflects whether the program is currently running.
    - ``toggle``: an on/off switch with separate ``on`` and ``off`` commands
      and a ``status`` command that reports the current state.
    """

    COMMAND = "command"
    APP = "app"
    TOGGLE = "toggle"


@dataclass
class Entry:
    """A single actionable item within a category."""

    name: str
    type: EntryType
    # For command / app entries:
    cmd: str | None = None
    # For toggle entries:
    on: str | None = None
    off: str | None = None
    # Optional command whose exit code (0 == active) reports current state.
    status: str | None = None
    description: str = ""
    # Ask for confirmation before running (use for anything that transmits,
    # cuts power, etc.).
    confirm: bool = False

    @property
    def detail(self) -> str:
        """Short human-readable summary of what this entry runs."""
        if self.type is EntryType.TOGGLE:
            return self.on or ""
        return self.cmd or ""


@dataclass
class Category:
    """A named group of entries, shown as one tab."""

    id: str
    title: str
    icon: str = ""
    description: str = ""
    entries: list[Entry] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.icon} {self.title}".strip()


@dataclass
class AppConfig:
    """Top-level parsed configuration."""

    name: str = "uConsole AIO Control"
    refresh_interval: int = 5
    categories: list[Category] = field(default_factory=list)
    # Path the config was loaded from (None when using built-in defaults).
    source_path: str | None = None

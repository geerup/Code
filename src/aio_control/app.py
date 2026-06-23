"""The Textual TUI for uConsole AIO Control."""

from __future__ import annotations

import asyncio
import os
import shlex
import subprocess
from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    RichLog,
    TabbedContent,
    TabPane,
)

from .config import ConfigError, install_default_config, load_config
from .models import AppConfig, Category, Entry, EntryType
from .runner import first_token, launch_detached, run_capture

# Status badge: symbol + Rich style.
_BADGES: dict[str, tuple[str, str]] = {
    "on": ("●", "bold green"),
    "off": ("○", "grey50"),
    "na": ("·", "grey37"),
    "busy": ("◐", "yellow"),
    "err": ("⚠", "bold red"),
}


def badge(state: str) -> Text:
    symbol, style = _BADGES.get(state, _BADGES["na"])
    return Text(symbol, style=style)


class CategoryTable(DataTable):
    """A DataTable that populates itself from a Category."""

    def __init__(self, category: Category, **kwargs) -> None:
        super().__init__(cursor_type="row", zebra_stripes=True, **kwargs)
        self.category = category

    def on_mount(self) -> None:
        self.add_column(" ", key="status", width=3)
        self.add_column("Name", key="name", width=26)
        self.add_column("Type", key="type", width=8)
        self.add_column("Command / detail", key="detail")
        for i, entry in enumerate(self.category.entries):
            self.add_row(
                badge("na"),
                entry.name,
                entry.type.value,
                entry.detail,
                key=str(i),
            )


class ConfirmScreen(ModalScreen[bool]):
    """A small yes/no confirmation dialog."""

    BINDINGS = [
        ("y", "yes", "Yes"),
        ("n", "no", "No"),
        ("escape", "no", "Cancel"),
    ]

    def __init__(self, name: str, command: str) -> None:
        super().__init__()
        self._name = name
        self._command = command

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(f"Run “{self._name}”?", id="confirm-title")
            yield Label(self._command, id="confirm-cmd")
            with Horizontal(id="confirm-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Run", variant="warning", id="ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "ok")

    def action_yes(self) -> None:
        self.dismiss(True)

    def action_no(self) -> None:
        self.dismiss(False)


class AIOControlApp(App):
    """Keyboard-driven control panel for the uConsole AIO board."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("space", "activate", "Run / launch"),
        ("x", "stop", "Stop"),
        ("r", "refresh", "Refresh"),
        ("R", "reload", "Reload cfg"),
        ("e", "edit_config", "Edit cfg"),
        ("c", "clear_log", "Clear log"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        # Tracks detached child processes keyed by "<category>:<row>".
        self.processes: dict[str, subprocess.Popen] = {}

    # -- composition -------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(id="tabs"):
            for cat in self.config.categories:
                with TabPane(cat.label, id=f"tab-{cat.id}"):
                    yield CategoryTable(cat, id=f"tbl-{cat.id}")
        yield RichLog(id="log", highlight=False, markup=False, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = self.config.name
        self.sub_title = self.config.source_path or "(built-in defaults)"
        self.log_line("uConsole AIO Control ready.", "bold cyan")
        self.log_line(
            "Tabs: ←/→   Move: ↑/↓   Run/launch: Space   Stop: x   "
            "Refresh: r   Reload cfg: R   Edit cfg: e",
            "grey62",
        )
        if self.config.refresh_interval > 0:
            self.set_interval(self.config.refresh_interval, self.refresh_statuses)
        self.refresh_statuses()

    # -- helpers -----------------------------------------------------------
    def log_line(self, text: str, style: str | None = None) -> None:
        log = self.query_one("#log", RichLog)
        log.write(Text(text, style=style) if style else text)

    def _active_category_id(self) -> str | None:
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        if not active:
            return None
        return active.removeprefix("tab-")

    def _current(self) -> tuple[str, int, Entry] | None:
        cid = self._active_category_id()
        if cid is None:
            return None
        try:
            table = self.query_one(f"#tbl-{cid}", CategoryTable)
        except Exception:
            return None
        row = table.cursor_row
        entries = table.category.entries
        if row is None or row < 0 or row >= len(entries):
            return None
        return cid, row, entries[row]

    def _set_badge(self, cid: str, row: int, state: str) -> None:
        try:
            table = self.query_one(f"#tbl-{cid}", CategoryTable)
            table.update_cell(str(row), "status", badge(state))
        except Exception:
            pass

    async def _compute_status(self, entry: Entry, key: str) -> str:
        """Return a badge state ('on'/'off'/'na') for an entry."""
        if entry.status:
            res = await run_capture(entry.status, timeout=8)
            return "on" if res.ok else "off"
        if entry.type is EntryType.APP:
            proc = self.processes.get(key)
            if proc is not None and proc.poll() is None:
                return "on"
            token = first_token(entry.cmd or "")
            if token:
                res = await run_capture(
                    f"pgrep -x {shlex.quote(token)} >/dev/null 2>&1", timeout=5
                )
                return "on" if res.ok else "off"
            return "off"
        # command (and toggles without a status command) carry no state.
        return "na"

    # -- status refresh ----------------------------------------------------
    @work(exclusive=True, group="refresh")
    async def refresh_statuses(self) -> None:
        async def one(cid: str, row: int, entry: Entry) -> None:
            state = await self._compute_status(entry, f"{cid}:{row}")
            self._set_badge(cid, row, state)

        tasks = [
            one(cat.id, i, entry)
            for cat in self.config.categories
            for i, entry in enumerate(cat.entries)
        ]
        if tasks:
            await asyncio.gather(*tasks)

    # -- actions -----------------------------------------------------------
    @work(group="action")
    async def action_activate(self) -> None:
        current = self._current()
        if current is None:
            return
        cid, row, entry = current
        key = f"{cid}:{row}"

        if entry.confirm:
            primary = entry.detail or entry.on or entry.cmd or ""
            ok = await self.push_screen_wait(ConfirmScreen(entry.name, primary))
            if not ok:
                self.log_line(f"✗ cancelled: {entry.name}", "grey50")
                return

        if entry.type is EntryType.COMMAND:
            await self._run_command(cid, row, entry)
        elif entry.type is EntryType.APP:
            await self._launch_app(cid, row, entry, key)
        elif entry.type is EntryType.TOGGLE:
            await self._toggle(cid, row, entry, key)

    async def _run_command(self, cid: str, row: int, entry: Entry) -> None:
        self.log_line(f"$ {entry.cmd}", "bold white")
        self._set_badge(cid, row, "busy")
        res = await run_capture(entry.cmd or "", timeout=120)
        if res.output:
            self.log_line(res.output)
        self.log_line(
            f"[exit {res.exit_code}]",
            "green" if res.ok else "red",
        )
        self._set_badge(cid, row, "on" if res.ok else "err")

    async def _launch_app(self, cid: str, row: int, entry: Entry, key: str) -> None:
        # If we already launched it and it is alive, just say so.
        existing = self.processes.get(key)
        if existing is not None and existing.poll() is None:
            self.log_line(
                f"• {entry.name} already running (pid {existing.pid})", "yellow"
            )
            return
        log_path = self._app_log_path(cid, row)
        try:
            proc = launch_detached(entry.cmd or "", log_path)
        except OSError as exc:
            self.log_line(f"⚠ failed to launch {entry.name}: {exc}", "bold red")
            self._set_badge(cid, row, "err")
            return
        self.processes[key] = proc
        self.log_line(
            f"▶ launched {entry.name}: {entry.cmd}  (pid {proc.pid})", "bold green"
        )
        self.notify(f"Launched {entry.name}")
        await asyncio.sleep(0.4)
        alive = proc.poll() is None
        self._set_badge(cid, row, "on" if alive else "err")
        if not alive:
            self.log_line(
                f"⚠ {entry.name} exited immediately (code {proc.returncode}) "
                f"- see {log_path}",
                "red",
            )

    async def _toggle(self, cid: str, row: int, entry: Entry, key: str) -> None:
        state = await self._compute_status(entry, key)
        turning_off = state == "on"
        cmd = entry.off if turning_off else entry.on
        verb = "off" if turning_off else "on"
        self.log_line(f"$ ({verb}) {cmd}", "bold white")
        self._set_badge(cid, row, "busy")
        res = await run_capture(cmd or "", timeout=60)
        if res.output:
            self.log_line(res.output)
        new_state = await self._compute_status(entry, key)
        self._set_badge(cid, row, new_state)
        self.notify(f"{entry.name}: {new_state}")

    @work(group="action")
    async def action_stop(self) -> None:
        current = self._current()
        if current is None:
            return
        cid, row, entry = current
        key = f"{cid}:{row}"

        if entry.type is EntryType.TOGGLE and entry.off:
            self.log_line(f"$ (off) {entry.off}", "bold white")
            await run_capture(entry.off, timeout=60)
            self._set_badge(cid, row, await self._compute_status(entry, key))
            return

        proc = self.processes.get(key)
        if proc is not None and proc.poll() is None:
            self._kill_process(proc)
            self.log_line(f"■ stopped {entry.name} (pid {proc.pid})", "yellow")
            self._set_badge(cid, row, "off")
            return

        if entry.type is EntryType.APP and entry.cmd:
            token = first_token(entry.cmd)
            res = await run_capture(f"pkill -x {shlex.quote(token)}", timeout=10)
            msg = "stopped" if res.ok else "nothing to stop"
            self.log_line(f"■ {msg}: {token}", "yellow")
            self._set_badge(cid, row, "off")
        else:
            self.log_line(f"• {entry.name}: nothing to stop", "grey50")

    @staticmethod
    def _kill_process(proc: subprocess.Popen) -> None:
        try:
            os.killpg(os.getpgid(proc.pid), 15)
        except (ProcessLookupError, PermissionError):
            try:
                proc.terminate()
            except ProcessLookupError:
                pass

    def action_refresh(self) -> None:
        self.refresh_statuses()

    def action_clear_log(self) -> None:
        self.query_one("#log", RichLog).clear()

    async def action_reload(self) -> None:
        try:
            cfg = load_config(self.config.source_path)
        except ConfigError as exc:
            self.log_line(f"⚠ reload failed: {exc}", "bold red")
            self.notify("Reload failed - see log", severity="error")
            return
        self.config = cfg
        await self.recompose()
        self.title = cfg.name
        self.sub_title = cfg.source_path or "(built-in defaults)"
        self.log_line("↻ config reloaded", "bold cyan")
        self.refresh_statuses()

    def action_edit_config(self) -> None:
        path = Path(self.config.source_path) if self.config.source_path else None
        if path is None:
            path = install_default_config()
            self.config.source_path = str(path)
            self.log_line(f"Created editable config at {path}", "cyan")
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
        try:
            with self.suspend():
                subprocess.call([editor, str(path)])
        except FileNotFoundError:
            self.log_line(
                f"⚠ editor '{editor}' not found - set $EDITOR", "bold red"
            )
            return
        # Reload after editing.
        self.call_later(self.action_reload)

    def _app_log_path(self, cid: str, row: int) -> str:
        base = Path(
            os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
        ) / "uconsole-aio" / "logs"
        base.mkdir(parents=True, exist_ok=True)
        return str(base / f"{cid}-{row}.log")

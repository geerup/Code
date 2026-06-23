"""Load and validate the AIO control YAML config.

Config resolution order (first match wins):

1. Explicit path passed on the command line / to :func:`load_config`.
2. ``$AIO_CONTROL_CONFIG`` environment variable.
3. ``$XDG_CONFIG_HOME/uconsole-aio/aio.yaml`` (or ``~/.config/...``).
4. The bundled ``default_config.yaml`` shipped with the package.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

import yaml

from .models import AppConfig, Category, Entry, EntryType


class ConfigError(ValueError):
    """Raised when a config file is structurally invalid."""


def user_config_path() -> Path:
    """Return the per-user config path (may not exist yet)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "uconsole-aio" / "aio.yaml"


def _resolve_path(explicit: str | os.PathLike[str] | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("AIO_CONTROL_CONFIG")
    if env:
        return Path(env).expanduser()
    user = user_config_path()
    if user.exists():
        return user
    return None


def _default_yaml_text() -> str:
    return resources.files("aio_control").joinpath("default_config.yaml").read_text(
        encoding="utf-8"
    )


def _normalize_keys(raw: dict) -> dict:
    """Repair YAML's boolean-key gotcha.

    In YAML 1.1 the bare words ``on``/``off``/``yes``/``no`` parse to booleans,
    so ``on:`` becomes the key ``True`` and ``off:`` the key ``False``. Map
    those back to the string keys we expect so users can write the natural
    ``on:`` / ``off:`` syntax without quoting.
    """
    if True not in raw and False not in raw:
        return raw
    fixed = dict(raw)
    if True in fixed and "on" not in fixed:
        fixed["on"] = fixed.pop(True)
    if False in fixed and "off" not in fixed:
        fixed["off"] = fixed.pop(False)
    return fixed


def _parse_entry(raw: dict, where: str) -> Entry:
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: entry must be a mapping, got {type(raw).__name__}")
    raw = _normalize_keys(raw)
    if "name" not in raw:
        raise ConfigError(f"{where}: entry is missing required 'name'")
    name = str(raw["name"])
    type_str = str(raw.get("type", "command")).lower()
    try:
        etype = EntryType(type_str)
    except ValueError:
        valid = ", ".join(t.value for t in EntryType)
        raise ConfigError(
            f"{where}: '{name}' has unknown type '{type_str}' (expected one of: {valid})"
        ) from None

    entry = Entry(
        name=name,
        type=etype,
        cmd=_opt_str(raw.get("cmd")),
        on=_opt_str(raw.get("on")),
        off=_opt_str(raw.get("off")),
        status=_opt_str(raw.get("status")),
        description=str(raw.get("description", "")),
        confirm=bool(raw.get("confirm", False)),
    )

    # Validate required fields per type.
    if etype in (EntryType.COMMAND, EntryType.APP) and not entry.cmd:
        raise ConfigError(f"{where}: '{name}' ({etype.value}) requires a 'cmd'")
    if etype is EntryType.TOGGLE and not (entry.on and entry.off):
        raise ConfigError(
            f"{where}: '{name}' (toggle) requires both 'on' and 'off' commands"
        )
    return entry


def _opt_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_category(raw: dict, index: int) -> Category:
    if not isinstance(raw, dict):
        raise ConfigError(f"category #{index}: must be a mapping")
    cid = _opt_str(raw.get("id")) or _opt_str(raw.get("title"))
    if not cid:
        raise ConfigError(f"category #{index}: requires an 'id' or 'title'")
    cid = cid.lower().replace(" ", "_")
    title = str(raw.get("title", cid))
    where = f"category '{title}'"
    entries_raw = raw.get("entries", []) or []
    if not isinstance(entries_raw, list):
        raise ConfigError(f"{where}: 'entries' must be a list")
    entries = [_parse_entry(e, where) for e in entries_raw]
    return Category(
        id=cid,
        title=title,
        icon=str(raw.get("icon", "")),
        description=str(raw.get("description", "")),
        entries=entries,
    )


def parse_config(data: dict, source_path: str | None = None) -> AppConfig:
    """Build an :class:`AppConfig` from a parsed YAML mapping."""
    if not isinstance(data, dict):
        raise ConfigError("top-level config must be a mapping")

    meta = data.get("meta", {}) or {}
    if not isinstance(meta, dict):
        raise ConfigError("'meta' must be a mapping")

    categories_raw = data.get("categories", []) or []
    if not isinstance(categories_raw, list):
        raise ConfigError("'categories' must be a list")
    if not categories_raw:
        raise ConfigError("config defines no categories")

    categories = [_parse_category(c, i) for i, c in enumerate(categories_raw)]

    try:
        refresh = int(meta.get("refresh_interval", 5))
    except (TypeError, ValueError):
        raise ConfigError("meta.refresh_interval must be an integer") from None
    refresh = max(0, refresh)

    return AppConfig(
        name=str(meta.get("name", "uConsole AIO Control")),
        refresh_interval=refresh,
        categories=categories,
        source_path=source_path,
    )


def load_config(path: str | os.PathLike[str] | None = None) -> AppConfig:
    """Load configuration, falling back to the bundled default."""
    resolved = _resolve_path(path)
    if resolved is not None:
        if not resolved.exists():
            raise ConfigError(f"config file not found: {resolved}")
        text = resolved.read_text(encoding="utf-8")
        source = str(resolved)
    else:
        text = _default_yaml_text()
        source = None

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {source or 'default config'}: {exc}") from exc

    return parse_config(data or {}, source_path=source)


def install_default_config(dest: Path | None = None, overwrite: bool = False) -> Path:
    """Write the bundled default config to the user config path.

    Returns the destination path. Refuses to overwrite unless asked.
    """
    target = Path(dest).expanduser() if dest else user_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return target
    target.write_text(_default_yaml_text(), encoding="utf-8")
    return target

# Guidance for Claude Code

This project is **uConsole AIO Control** — a Textual TUI that controls the
HackerGadgets v2 AIO (SDR / LoRa / GPS / USB rail) on a ClockworkPi uConsole.

The most common request will be **"add a command/app/toggle"**. That almost
never means writing Python — it means appending an entry to the YAML config.

## Project layout

```
src/aio_control/
  models.py            # Entry / Category / AppConfig dataclasses
  config.py            # YAML load + validation (the schema lives here)
  runner.py            # shell command execution (capture + detached launch)
  app.py               # the Textual TUI
  cli.py               # `aioctl` entry point
  default_config.yaml  # seed config; copied to ~/.config/uconsole-aio/aio.yaml
tests/                 # pytest suite (run: pytest)
```

## Adding to the control surface (the usual task)

Edit the user's config at `~/.config/uconsole-aio/aio.yaml` if it exists,
otherwise edit `src/aio_control/default_config.yaml`. Add an entry under the
right category's `entries:` list. Entry schema:

| type      | required keys | optional keys                         |
|-----------|---------------|---------------------------------------|
| `command` | `name`, `cmd` | `status`, `description`, `confirm`    |
| `app`     | `name`, `cmd` | `status`, `description`, `confirm`    |
| `toggle`  | `name`, `on`, `off` | `status`, `description`, `confirm` |

- `command` — runs once, output goes to the log pane.
- `app` — launched detached (GUI / long-running). Status falls back to
  `pgrep -x <program>` when no `status` is given.
- `toggle` — `status` should exit `0` when the thing is **on**; that drives the
  badge and decides whether `Space` runs `on` or `off`.
- `confirm: true` — set this for anything that **transmits**, cuts power, or is
  otherwise risky.

### YAML gotcha (important)

`on:` / `off:` are valid here — the parser repairs YAML's boolean-key quirk
(`on`/`off`/`yes`/`no` → booleans). You do **not** need to quote them, but if
you ever see a toggle "missing on/off", that quirk is why; quoting the keys
(`"on":`) also works.

## After editing

1. Validate: `aioctl --check` (must print OK with the new count).
2. If you changed Python, run `pytest`.
3. In a running app the user presses `R` to hot-reload the config.

## Conventions

- Keep commands shell-compatible (pipes/redirects fine; they run via `sh -c`).
- Don't hardcode device specifics you can't know — leave editable placeholders
  like `/dev/ttyUSB0`, hub `-p <port>`, `--frequency` and note them in
  `description`.
- Match the existing comment density and style in `default_config.yaml`.

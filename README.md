# uConsole AIO Control

A keyboard-driven **terminal control panel** for the
[ClockworkPi uConsole](https://www.clockworkpi.com/uconsole) (Debian *trixie*)
and the **HackerGadgets "v2 AIO"** all-in-one radio board — SDR, LoRa, GPS and
the switchable USB power rail — all from one screen.

It launches your SDR / GPS / LoRa / satellite / weather apps, runs one-shot
commands, and exposes on/off **toggles** for the things you turn on and off
around satellites, radio, weather and GPS. Everything it shows is defined in a
single, editable YAML file, so the command set grows over time — including
commands you generate with **Claude Code** — without touching any Python.

```
┌ uConsole AIO Control ───────────────────────────────────────┐
│  SDR   GPS   LoRa   USB Rail   Satellites   Weather   Radio  │
│  ●  HackRF Info        command   hackrf_info                 │
│  ○  gpsd daemon        toggle    sudo systemctl start gpsd   │
│  ●  rtl_433 sensors    toggle    rtl_433 -F json             │
│  ·  GQRX               app       gqrx                        │
├──────────────────────────────────────────────────────────────┤
│ $ hackrf_info                                                │
│ Found HackRF / Serial: 0x...                                 │
└──────────────────────────────────────────────────────────────┘
```

## Why a TUI

The uConsole is a keyboard handheld with a short 1280×480 screen. A
[Textual](https://textual.textualize.io/) TUI is light on the ARM CPU, runs
fine over SSH, and is fully keyboard-driven — no mouse needed.

## Install

On the uConsole (Debian trixie):

```bash
git clone https://github.com/geerup/Code.git uconsole-aio
cd uconsole-aio
./install.sh          # creates a venv, installs the app + an editable config
```

Or manually:

```bash
python3 -m venv ~/.venvs/aio
~/.venvs/aio/bin/pip install .
~/.venvs/aio/bin/aioctl --init     # write the default config you can edit
```

## Run

```bash
aioctl                     # launch the TUI
aioctl -c ./my-aio.yaml    # use a specific config
aioctl --check             # validate config, print a summary, exit
aioctl --init              # write the default config to ~/.config/uconsole-aio/aio.yaml
aioctl --config-path       # print where the config lives
```

## Keys

| Key        | Action                                            |
|------------|---------------------------------------------------|
| `←` / `→`  | Switch category tab                               |
| `↑` / `↓`  | Move between entries                              |
| `Space`    | Run command / launch app / flip toggle            |
| `x`        | Stop a launched app or switch a toggle **off**    |
| `r`        | Refresh status badges now                          |
| `R`        | Reload the config file                             |
| `e`        | Edit the config in `$EDITOR`, then reload          |
| `c`        | Clear the log pane                                 |
| `q`        | Quit                                              |

Status badges: `●` on/running · `○` off/stopped · `·` no persistent state ·
`◐` working · `⚠` error.

## The config is the app

Everything lives in `~/.config/uconsole-aio/aio.yaml` (seeded from
[`src/aio_control/default_config.yaml`](src/aio_control/default_config.yaml)).
Each category is a tab; each entry is one of three types:

```yaml
categories:
  - id: sdr
    title: SDR
    icon: "📡"
    entries:
      # run once, show output in the log pane
      - name: HackRF Info
        type: command
        cmd: hackrf_info

      # launch a long-running / GUI program, detached from the TUI
      - name: GQRX
        type: app
        cmd: gqrx

      # an on/off switch; `status` (exit 0 == on) drives the badge
      - name: gpsd daemon
        type: toggle
        on:  sudo systemctl start gpsd
        off: sudo systemctl stop gpsd
        status: systemctl is-active --quiet gpsd
        confirm: true        # ask before running (use for TX / power cuts)
```

Commands run through the shell, so pipes, redirects and env vars all work.
Adjust device paths (`/dev/ttyUSB0`), hub ports and frequencies to match your
AIO wiring, then press `R` in the app to reload.

### Default toolchain targeted

- **SDR** — `hackrf_info`, `SoapySDRUtil`, gqrx, SDR++, CubicSDR, SDRangel
- **GPS** — `gpsd`, `cgps`, `gpsmon`, raw NMEA via `gpspipe`, FoxtrotGPS
- **LoRa** — Meshtastic CLI, serial console (`picocom`), raw AT commands
- **USB rail** — `uhubctl` per-port power toggles
- **Satellites** — Gpredict, SatDump, `predict`, TLE updates
- **Weather** — `noaa-apt`, `rtl_433`, SatDump live APT
- **Radio** — `rtl_fm` FM, `dump1090` ADS-B, Direwolf APRS, `rtl_power` sweeps

These tools aren't bundled — install what you use (`apt install gpsd gpsd-clients
rtl-433 ...`, build SatDump, etc.). Missing tools simply show as `off`/error
when run; they never crash the app.

## Adding commands with Claude Code

This repo is set up so you can ask Claude Code to extend the control surface:

> "Add a Weather entry that decodes Meteor-M2 LRPT with SatDump at 137.9 MHz."

Claude Code appends a well-formed entry to your `aio.yaml`; press `R` to reload.
See [`CLAUDE.md`](CLAUDE.md) for the schema rules it follows.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).

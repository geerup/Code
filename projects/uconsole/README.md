# uconsole

Build log and operations guide for a heavily-modified ClockworkPi uConsole (Raspberry Pi
CM4) portable Linux device: AIO v2 upgrade, NVMe boot, RF/antenna work, power profiling,
and an offline-capable software stack.

**Status:** running (device is real; repo docs being imported from operator's guides)

This repo documents a real, working device. The prose here is a scaffold: section
structure and the factual, independently-verifiable engineering details are in place, and
the operator's own build log, measurements, and debugging narrative are being imported
from their setup guides. Anywhere the text depends on the operator's specific hardware
run, it is marked `> OPERATOR: import ...` rather than invented.

## Overview

The uConsole is a CM4-based handheld Linux computer. This unit has been taken well past
the stock configuration:

- **Compute/memory:** ClockworkPi AIO v2 mainboard upgrade + CM4 module (see
  [hardware-mods.md](docs/hardware-mods.md)).
- **Storage:** NVMe SSD via an M.2 adapter board, with the CM4 EEPROM boot order set so
  the device boots SD-first and falls back to NVMe (see
  [boot-and-storage.md](docs/boot-and-storage.md)).
- **RF:** external antenna work including a 7-antenna mount for the onboard/USB radios
  (see [hardware-mods.md](docs/hardware-mods.md)).
- **Power:** bench profiling of idle and load draw for battery-runtime planning (see
  [power-profiling.md](docs/power-profiling.md)).
- **Offline stack:** local-first services so the device is useful without connectivity.

## Hardware config

Summary table; full detail and install notes in
[docs/hardware-mods.md](docs/hardware-mods.md).

| Subsystem | Component | Notes |
|-----------|-----------|-------|
| Mainboard | ClockworkPi AIO v2 | `> OPERATOR: import exact revision/order` |
| Compute | Raspberry Pi CM4 | `> OPERATOR: import RAM/eMMC/WiFi variant` |
| Storage adapter | M.2 NVMe board | `> OPERATOR: import board model` |
| SSD | NVMe M.2 2280/2242 | `> OPERATOR: import model + capacity` |
| RF | 7-antenna mount | `> OPERATOR: import antenna/radio mapping` |

## Boot / storage rationale

The CM4 EEPROM boot order is set to `BOOT_ORDER=0xf41`, which the firmware reads
right-to-left: try **SD card (1)** first, then **NVMe (4)**, then **restart the sequence
(f)**. This is a deliberate "SD-first with NVMe fallback" choice.

**Decision — SD-first, NVMe-fallback (`0xf41`), not NVMe-first:**
Keeping the SD slot as the first boot source means a bootable SD card always wins. That
makes recovery trivial — to repair or re-image, insert a known-good SD card and the device
boots it without touching EEPROM or the installed NVMe. The everyday OS still lives on the
faster, higher-endurance NVMe, which is reached automatically whenever no bootable SD card
is present. The tradeoff is that normal boots depend on the slot being empty; the recovery
guarantee is worth that. Full walkthrough and the EEPROM edit procedure are in
[docs/boot-and-storage.md](docs/boot-and-storage.md).

## Power results

Bench power profiling method and results table live in
[docs/power-profiling.md](docs/power-profiling.md). The operator's claimed idle figure is
**~2.75–3 W** (to be confirmed against the imported measurement log — treat as claimed,
not yet reproduced in this repo).

## Notable debugging

The device's AC1200-class USB WiFi adapter failed to enumerate under specific conditions;
the root-cause investigation and fix are written up in
[docs/ac1200-debug.md](docs/ac1200-debug.md). This is the headline "root-caused a USB
enumeration failure" story.

## Offline capability

The device runs a local-first software stack so it stays useful with no network. Details
are imported alongside the setup guide.

> OPERATOR: import offline-stack service list from your setup reference.

## Documents

- [docs/setup-guide.md](docs/setup-guide.md) — the living setup/operations guide.
- [docs/hardware-mods.md](docs/hardware-mods.md) — AIO v2, CM4 adapter, NVMe board, antennas.
- [docs/boot-and-storage.md](docs/boot-and-storage.md) — EEPROM boot order and storage.
- [docs/power-profiling.md](docs/power-profiling.md) — power method + measurements.
- [docs/ac1200-debug.md](docs/ac1200-debug.md) — USB enumeration root-cause writeup.

## License

MIT — see [LICENSE](LICENSE).

# Setup / operations guide

The living setup and operations guide for this uConsole build. This file is the merged,
cleaned home for the operator's own setup reference and the two markdown build guides.

> OPERATOR: import from your setup reference (`~/Desktop/uConsole_Setup_Reference.txt`
> and `/mnt/user-data/outputs/*.md`). Do not paraphrase from memory — paste the real
> steps you ran so the guide matches the device.

## OS image and base install

> OPERATOR: import the exact OS image (distro, kernel, image date) and the flashing
> procedure you used.

## First-boot configuration

> OPERATOR: import your first-boot steps (locale, user, hostname policy, package
> baseline). Scrub any real hostnames, SSIDs, or tailnet references before import.

## Networking bring-up

> OPERATOR: import how the radios are brought up and which interfaces map to which
> antenna. No real SSIDs or WiFi credentials — reference `wpa_supplicant`/NetworkManager
> config by placeholder only.

## Software stack

> OPERATOR: import the installed package/service list and any custom units.

## Related documents

- [hardware-mods.md](hardware-mods.md) — physical modifications.
- [boot-and-storage.md](boot-and-storage.md) — EEPROM boot order and storage layout.
- [power-profiling.md](power-profiling.md) — power measurement method + results.
- [ac1200-debug.md](ac1200-debug.md) — USB enumeration root-cause writeup.

# Boot and storage

How this device boots and where the OS lives: SD-first with NVMe fallback, set through
the CM4 EEPROM boot order.

## What `BOOT_ORDER=0xf41` means

The Raspberry Pi CM4 bootloader (stored in the EEPROM) reads `BOOT_ORDER` as a sequence
of 4-bit fields, evaluated **right-to-left** (least-significant nibble first). Each
nibble names a boot mode the firmware tries in turn:

| Nibble | Boot mode (common values) |
|--------|---------------------------|
| `0x1`  | SD card                   |
| `0x4`  | NVMe (PCIe)               |
| `0x6`  | USB mass storage          |
| `0xf`  | Restart the sequence (loop back to the first field) |

So `0xf41` is processed as:

1. `1` — try the **SD card** first.
2. `4` — if no bootable SD card, try **NVMe**.
3. `f` — if neither succeeded, **restart the sequence** and keep retrying.

This is a deliberate "SD-first, NVMe-fallback" order.

## Why SD-first with NVMe fallback (decision + rationale)

**Decision:** keep the SD slot as the first boot source even though the everyday OS
lives on NVMe.

**Rationale:** making a bootable SD card always win gives a trivial, hardware-level
recovery path. To repair or re-image, insert a known-good SD card and the device boots
it — no EEPROM edit, no disturbing the installed NVMe system. Day to day the slot is
empty, so the firmware falls straight through to the faster, higher-endurance NVMe. The
alternative (NVMe-first) boots without a card present but turns recovery into an EEPROM
edit under duress, exactly when you least want to reflash bootloader config. The cost of
SD-first is that a stray bootable card silently preempts the NVMe OS; keeping the slot
empty in normal operation is the discipline that buys the recovery guarantee.

The trailing `f` matters too: rather than dropping to a non-boot state if both fail
(e.g. during a cold boot before a disk spins up or a card is fully seated), the
bootloader loops and retries the whole order.

## EEPROM edit procedure

The boot order is written into the CM4 bootloader EEPROM with `rpi-eeprom-config`. The
generic shape of the procedure:

```bash
# View the current configuration
rpi-eeprom-config

# Edit into a file, set BOOT_ORDER=0xf41, then apply on next reboot
rpi-eeprom-config --edit
```

> OPERATOR: import from your setup reference — the exact commands, bootloader version,
> any `rpi-eeprom-update` steps, and the confirmation output you saw. Do not invent
> version strings or logs.

## Storage layout

> OPERATOR: import the partition/filesystem layout on the NVMe (and SD, if used),
> mount points, and any tuning (fstab options, swap policy). Scrub UUIDs/serials that
> could identify the specific drive if you consider them sensitive.

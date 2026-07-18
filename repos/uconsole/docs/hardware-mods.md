# Hardware modifications

Physical modifications taken past the stock ClockworkPi uConsole configuration. Each
section below is a skeleton; the operator's exact parts, revisions, and install notes
are imported from the setup reference.

## AIO v2 mainboard upgrade

The ClockworkPi AIO v2 mainboard replaces the stock uConsole carrier.

> OPERATOR: import from your setup reference — exact board revision, why you upgraded,
> install order, and any gotchas (ribbon seating, standoff/clearance issues, firmware).

## CM4 module / adapter

> OPERATOR: import from your setup reference — CM4 variant (RAM / eMMC vs. Lite / WiFi),
> the CM4 adapter used, and any orientation or seating notes.

## NVMe adapter board

The M.2 NVMe adapter board provides the primary storage path. Boot-order interaction is
documented separately in [boot-and-storage.md](boot-and-storage.md).

> OPERATOR: import from your setup reference — adapter board model, M.2 form factor
> supported (2230/2242/2280), PCIe lane/link notes, and physical fit/clearance.

## 7-antenna mount and RF work

An external multi-antenna mount replaces the stock internal antenna arrangement to serve
the onboard and USB radios.

> OPERATOR: import from your setup reference — antenna-to-radio mapping (which connector
> feeds which interface), connector types (u.FL / RP-SMA), cable routing, and any device
> tree parameters needed to select an antenna path. See
> [../config/uconsole-antenna.txt](../config/uconsole-antenna.txt) for the generic
> `dtparam=ant2` example.

## Assembled configuration summary

> OPERATOR: import the final parts list. Keep it factual; no vendor marketing copy.

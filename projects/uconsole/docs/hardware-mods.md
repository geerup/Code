# Hardware modifications

Physical modifications taken past the stock ClockworkPi uConsole configuration. Each
section below is an outline; the exact parts, revisions, and install notes for this build
are still being written up from my notes.

## AIO v2 mainboard upgrade

The ClockworkPi AIO v2 mainboard replaces the stock uConsole carrier.

> _To be added: exact board revision, why I upgraded, install order, and any gotchas
> (ribbon seating, standoff/clearance issues, firmware)._

## CM4 module / adapter

> _To be added: CM4 variant (RAM / eMMC vs. Lite / WiFi), the CM4 adapter used, and any
> orientation or seating notes._

## NVMe adapter board

The M.2 NVMe adapter board provides the primary storage path. Boot-order interaction is
documented separately in [boot-and-storage.md](boot-and-storage.md).

> _To be added: adapter board model, M.2 form factor supported (2230/2242/2280), PCIe
> lane/link notes, and physical fit/clearance._

## 7-antenna mount and RF work

An external multi-antenna mount replaces the stock internal antenna arrangement to serve
the onboard and USB radios.

> _To be added: antenna-to-radio mapping (which connector feeds which interface),
> connector types (u.FL / RP-SMA), cable routing, and any device-tree parameters needed
> to select an antenna path._ See
> [../config/uconsole-antenna.txt](../config/uconsole-antenna.txt) for the generic
> `dtparam=ant2` example.

## Assembled configuration summary

> _Final parts list to be added._

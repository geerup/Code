# AC1200 USB WiFi enumeration — root-cause writeup

The device's AC1200-class USB WiFi adapter failed to enumerate under specific
conditions. This is the "root-caused a USB enumeration failure" story; the structure of
the investigation is below, with my specific observations to be written up from my notes.

## Symptom

> _To be added: the exact failure I observed (adapter absent from `lsusb`, present but no
> `wlanX` interface, intermittent disappearance, dmesg errors, enumeration only in some
> ports/power states), with the real `dmesg`/`lsusb` lines rather than a reconstruction._

## Hypotheses considered

List the candidate causes weighed during the investigation and how each was tested or
ruled out. Typical axes for a USB enumeration failure on a CM4-class device:

- **Power delivery** — adapter's inrush/steady current exceeding what the port budget
  supplies (especially with the AIO board + NVMe drawing concurrently).
- **USB topology / hub** — which physical port and whether an internal hub or the
  adapter's own mode-switch is involved.
- **Driver / firmware** — missing kernel module or firmware blob for the specific
  chipset; USB mode-switch (cdrom-emulation) not completing.
- **Enumeration timing** — device not ready within the window at cold boot vs. hotplug.

> _To be added: which of these applied, with the evidence for and against each._

## Method

> _To be added: the diagnostic steps I actually ran — e.g. `lsusb -t` for topology,
> `dmesg -w` during hotplug, `usb-devices`, power measurement per state, testing across
> ports/power conditions — with the real command output._

## Root cause

> _To be added: the confirmed root cause, the single finding the evidence converged on,
> tied back to the specific observations above._

## Fix

> _To be added: the fix I applied and how I verified it held (the adapter now enumerates
> reliably across the conditions that previously failed), including any config change,
> firmware/module install, or power-path change._

## Takeaway

> _To be added: one or two lines on the general lesson (e.g. enumeration failures on
> constrained SBCs are often power-budget or timing problems masquerading as driver
> problems)._

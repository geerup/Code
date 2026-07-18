# AC1200 USB WiFi enumeration — root-cause writeup

The device's AC1200-class USB WiFi adapter failed to enumerate under specific
conditions. This is the "root-caused a USB enumeration failure" story; the structure of
the investigation is below, with the operator's specific observations imported from the
setup reference.

## Symptom

> OPERATOR: import from your setup reference — the exact failure. What did you observe?
> (adapter absent from `lsusb`, present but no `wlanX` interface, intermittent
> disappearance, dmesg errors, enumeration only in some ports/power states). Paste the
> real `dmesg`/`lsusb` lines you saw — do not reconstruct them from memory.

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

> OPERATOR: import which of these applied, with the evidence for and against each.

## Method

> OPERATOR: import the diagnostic steps you actually ran — e.g. `lsusb -t` for topology,
> `dmesg -w` during hotplug, `usb-devices`, power measurement per state, testing across
> ports/power conditions. Keep the real command output; scrub nothing but genuine
> secrets (there should be none in USB enumeration output).

## Root cause

> OPERATOR: import the confirmed root cause — the single finding the evidence converged
> on. State it plainly and tie it back to the specific observations above.

## Fix

> OPERATOR: import the fix you applied and how you verified it held (the adapter now
> enumerates reliably across the conditions that previously failed). Include any config
> change, firmware/module install, or power-path change.

## Takeaway

> OPERATOR: one or two lines on the general lesson (e.g. enumeration failures on
> constrained SBCs are often power-budget or timing problems masquerading as driver
> problems). This is the line an interviewer remembers.

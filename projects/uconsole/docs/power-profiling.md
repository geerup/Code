# Power profiling

Method and results for bench power measurement of the device, used for battery-runtime
planning.

## Why measure

Battery runtime is set by draw at each operating state, not by a single "typical" number.
Profiling idle vs. load lets you size expected runtime from the pack capacity and decide
which subsystems (radios, display backlight, NVMe) are worth gating when on battery.

## Method

> _Specifics of the measurement rig to be added. The structure below is the intended
> method; the bracketed items are what remains to be filled in._

1. **Instrument:** [inline USB power meter / bench PSU with current readout / other —
   specify make/model and its resolution and accuracy].
2. **Measurement point:** [where in the power path the meter sits — e.g. USB-C input
   upstream of the charger, or battery terminal].
3. **Conditions per reading:** display brightness, radios on/off, CPU governor, and what
   workload defines "idle" vs. "load".
4. **Settling / sampling:** how long you let each state settle and whether the figure is
   an instantaneous read or an average over a window.
5. **Repeat** each state and record the spread, not just one number.

## Measurements

> OPERATOR: fill measured values. Do not publish this table until the numbers are your
> own real readings — no placeholder numbers should ship as if measured.

| State                         | Display | Radios | Governor    | Power (W) | Notes |
|-------------------------------|---------|--------|-------------|-----------|-------|
| Idle                          |         |        |             |           |       |
| Idle (screen off)             |         |        |             |           |       |
| Light load (browsing/editing) |         |        |             |           |       |
| Sustained CPU load            |         |        |             |           |       |
| WiFi active transfer          |         |        |             |           |       |

## Claimed result (pending confirmation)

The operator's claimed idle figure is **~2.75–3 W**. This is recorded here as the
operator's stated result and is **pending confirmation** against the imported
measurement log — it has not been reproduced within this repo. Treat it as claimed, not
verified, until the measurement table above is filled from the real log.

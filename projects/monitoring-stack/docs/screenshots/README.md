# Screenshots

Real dashboard screenshots go here and are linked from the top-level `README.md`.

These must be genuine captures from the running stack — do not fabricate or mock up
dashboards that were never live. An empty directory is more honest than a faked image
while the stack is still `in progress`.

## Before adding an image, scrub it

- **Hostnames / instance labels:** blur or crop any real overlay hostnames, FQDNs, or
  `instance=` labels. Use placeholder names where possible before capturing.
- **IP addresses:** no overlay (`100.x`) or LAN addresses visible in panels, variables,
  or tooltips.
- **Anything else identifying:** account emails in the top-right user menu, org names,
  custom titles that leak topology.

Suggested files, once captured:

- `node-health.png` — CPU / memory / filesystem overview
- `disk-smart.png` — SMART attributes and self-assessment per device

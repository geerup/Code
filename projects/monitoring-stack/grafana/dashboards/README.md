# Grafana dashboards

Exported dashboard JSON lives here. Prometheus is the data source; import these in
Grafana (Dashboards → Import → Upload JSON) after adding the Prometheus data source at
`http://prometheus:9090`.

## Exporting your own dashboards

The real dashboards for this stack are exported from the running Grafana, not committed
by hand:

1. In Grafana, open the dashboard → Share → Export → **Export for sharing externally**
   (this templates the data source as `${DS_PROMETHEUS}` instead of a hard UID).
2. Save the JSON here with a descriptive name, e.g. `node-health.json`,
   `disk-smart.json`.
3. Before committing, scrub anything host-specific: real instance/hostname labels in
   template variable defaults, saved annotations, or panel titles. Replace with
   placeholders (`node.example.internal`) or generic text.

Do not paste dashboard JSON claimed to come from a running system unless it actually was
exported from one — an interviewer may ask you to open the live board.

## `starter-node-health.json` — starter template

`starter-node-health.json` in this directory is a **minimal starter template**, not a
capture from a running system. It contains three basic node_exporter panels (CPU busy,
memory used, root filesystem used) to give a working import target on a fresh Grafana.
Replace it with your real exported dashboards once the stack has been running and you have
boards worth showing.

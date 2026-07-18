# Kiwix Setup

How the local Kiwix server behind `guide.html` is set up: binary install on ARM64,
ZIM download/management, and running a full offline Wikipedia mirror from local
storage.

## 1. Installing kiwix-serve (ARM64 static binary)

Kiwix publishes prebuilt static binaries for Linux (x86_64 and ARM64), so on
ARM64 hardware (e.g. a Raspberry Pi or an ARM SBC) there's no need to build from
source.

```bash
# Download the ARM64 static build (check https://download.kiwix.org/release/kiwix-tools/
# for the current version/filename).
curl -LO https://download.kiwix.org/release/kiwix-tools/kiwix-tools_linux-aarch64-<version>.tar.gz

tar xzf kiwix-tools_linux-aarch64-<version>.tar.gz
sudo install -m 755 kiwix-tools_linux-aarch64-<version>/kiwix-serve /usr/local/bin/kiwix-serve

kiwix-serve --version
```

No runtime dependencies beyond the binary itself — this is what makes it a good fit
for low-power ARM devices dedicated to serving a local reference library.

## 2. ZIM file layout

ZIM is Kiwix's single-file archive format — one ZIM per site/dataset (a Wikipedia
mirror, a Stack Exchange site, Project Gutenberg, etc.), fully self-contained
including any images and search index.

Recommended layout (placeholder paths — adjust to your storage):

```
/path/to/zim-library/
├── wikipedia_en_all_maxi_<date>.zim
├── stackoverflow.com_en_all_<date>.zim
└── gutenberg_en_all_<date>.zim
```

Keep ZIMs on their own volume/mount if serving a full Wikipedia mirror — see storage
note below.

## 3. Downloading and updating ZIMs

Kiwix hosts a public library of prebuilt ZIMs:

```bash
# Browse available ZIMs
curl -s https://library.kiwix.org/catalog/v2/entries | less

# Download a specific ZIM directly (example, not a live URL)
curl -LO https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi_<date>.zim
```

ZIMs are versioned by date and refreshed periodically upstream. There's no built-in
auto-update mechanism in `kiwix-serve` itself — updating means downloading a newer ZIM
and swapping the file (verify checksums when provided, then replace the old file and
restart `kiwix-serve` or point it at the new filename).

## 4. Serving full Wikipedia from NVMe

The full "all + images" Wikipedia ZIM is tens of gigabytes. Two things matter for
serving it well from a small ARM device:

- **Storage medium:** an SD card handles this poorly under sustained random reads
  (search queries hit the ZIM's internal index across the whole file). Putting the ZIM
  library on NVMe (even over a USB3/PCIe adapter on a board without native NVMe)
  removes that bottleneck and keeps search latency reasonable.
- **Don't commit ZIMs to git.** They're binary, multi-gigabyte, and reproducible from
  the public Kiwix catalog — reference the download source instead (see above), never
  vendor the archive itself into this repo.

## 5. Running the server

```bash
kiwix-serve --port=8080 /path/to/zim-library/*.zim
```

- `--port` — defaults to 80; use an unprivileged port unless running as root/with
  `setcap`.
- Multiple ZIMs can be passed at once (glob or space-separated); `kiwix-serve` exposes
  each under its own path and a combined search.
- `--customindex=/path/to/guide.html` — serve a custom landing page (this repo's
  `guide.html`) instead of Kiwix's default library index.

For always-on serving, run it under a process supervisor (systemd unit, e.g.) rather
than a foreground shell — that setup is host-specific and left out of this repo's
generic guide.

## Notes / gotchas

- `kiwix-serve` binds to all interfaces by default — restrict with a firewall rule or
  reverse proxy if this box is reachable beyond your own network.
- Full Wikipedia ZIMs are large enough that download interruptions matter; prefer a
  download tool that supports resume (`curl -C -`, `aria2c`) over a plain single-shot
  fetch.

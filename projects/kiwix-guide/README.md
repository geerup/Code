# kiwix-guide

A themed HTML front-end for a self-hosted Kiwix server — offline knowledge
infrastructure. Kiwix serves whole websites (Wikipedia, Stack Exchange, Project
Gutenberg, etc.) from local ZIM archive files with no internet connection required;
this repo is the landing page that ties those archives together into one browsable
"library" instead of a bare directory listing from `kiwix-serve`.

Status: in progress (setup docs ready; themed front-end still to be added)

## What it is

`guide.html` is a static, single-page front-end that links out to the ZIM libraries
served by a local `kiwix-serve` instance — search across archives, jump straight to
Wikipedia, Stack Exchange dumps, or reference material, without needing a network
connection. It's meant to sit in front of `kiwix-serve` rather than replace it.

## Screenshot

*(placeholder — a screenshot of the live guide goes here once the front-end is added;
scrub any visible hostnames or local IPs from the image before committing)*

`docs/screenshot.png` — not yet added.

## How to point it at kiwix-serve

1. Run `kiwix-serve` pointed at your ZIM library directory (see
   `docs/kiwix-setup.md` for the ARM64 static-binary setup used here):
   ```bash
   kiwix-serve --port=8080 /path/to/zim-library/*.zim
   ```
2. Open `guide.html` in a browser and confirm the links in it match the `kiwix-serve`
   base URL — by default that's `http://localhost:8080`. The shipped `guide.html` is a
   placeholder; see the comment inside it for the fields the real front-end needs to fill in.
3. For serving `guide.html` itself, any static file server works (`kiwix-serve` can also
   serve a custom landing page via its `--customindex` option; see `kiwix-setup.md`).

Everything here is meant to run against `localhost` or a private LAN address you
control — no external dependency once `kiwix-serve` and the ZIMs are local.

## ZIM notes

- ZIM files are the compressed archive format Kiwix reads — one file per site/dataset
  (e.g. a full Wikipedia mirror, a Stack Exchange site, Project Gutenberg).
- ZIMs are large (a full Wikipedia-with-images ZIM runs into the tens of gigabytes) —
  they are intentionally **not** committed to this repo. See `docs/kiwix-setup.md` for
  where to download them and how they're managed on-disk.
- See `docs/kiwix-setup.md` for the full setup: binary install, ZIM download/update
  workflow, and running a full offline Wikipedia mirror off local storage.

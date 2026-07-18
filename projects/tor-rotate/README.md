# tor-rotate

Shell helpers for rotating Tor circuits over the control port, with **client-side
NEWNYM rate limiting** so the loop never sends signals faster than Tor will actually
honor — plus a writeup of the SOCKS5 DNS-leak footgun that quietly defeats the whole
exercise.

**Status: in progress** — the `rotate` / `rotaton` / `rotatoff` functions come from
working shell functions used interactively; they have been formalized here into a single
sourceable/executable script. The documentation is complete; packaging (install path,
tests) is still being firmed up.

## Problem: metadata leakage

Using Tor hides the *content* of your traffic, but two kinds of metadata routinely leak
around it:

1. **Circuit persistence.** By default a set of streams shares a circuit (and exit
   relay) for minutes at a time. For some workflows you want to churn the exit more
   aggressively so that separate actions do not all correlate to one exit relay.
2. **DNS resolution outside the tunnel.** If your client resolves hostnames locally
   before handing an IP to the SOCKS proxy, it broadcasts *what you are connecting to* to
   your ISP's resolver in plaintext — no matter how many circuits you rotate through.

This repo addresses the first with an honest rotation helper, and documents the second
because it is the failure that actually deanonymizes people.

## What this does

`tor-rotate.sh` talks to the Tor control port and issues `SIGNAL NEWNYM` to request new
circuits. It provides:

- `rotate` — one-shot: request a new circuit now (rate-limited).
- `rotaton [SECONDS]` — start a background loop that rotates every N seconds
  (default 30, floored at 10).
- `rotatoff` — stop the loop.

It authenticates to the control port via **cookie authentication** (auto-detected at the
usual paths, or `TOR_COOKIE_PATH`) or a **control password** (`TOR_CONTROL_PASSWD`), and
it can be either **sourced** as functions in your shell or **run as a CLI**.

## NEWNYM rate limiting (why the loop is honest)

Tor coalesces `NEWNYM` signals that arrive within ~10 seconds of each other — a compiled
constant, not a config option. Send five signals in five seconds and Tor answers
`250 OK` to all five but performs roughly **one** rotation; the other four are folded
into the coalescing window and silently discarded. A naive `while ...; sleep 1` loop thus
*looks* like it rotates every second while actually rotating about every ten.

`tor-rotate.sh` gates on the client side: it records the timestamp of each `NEWNYM` it
sends and refuses to send another until `TOR_ROTATE_MIN_INTERVAL` (default 10s) has
elapsed. One-shot `rotate` prints `throttled` and exits non-zero inside the window;
`rotaton` clamps any sub-floor period up to the floor. The number of signals sent equals
the number of rotations Tor will honor, so the logs tell the truth.

Full explanation: [`docs/newnym-rate-limit.md`](docs/newnym-rate-limit.md).

### Decision + rationale: rate-limit on the client, don't hammer NEWNYM

The obvious approach is to send `NEWNYM` as fast as you want a new circuit and let Tor
sort it out. I gate it client-side instead, for three reasons:

- **Truthful telemetry.** Because Tor returns `250 OK` even for coalesced signals, a
  loop that hammers the port produces logs that *claim* N rotations while delivering ~N/10.
  Anyone reasoning about correlation risk from those logs is reasoning from fiction.
  Gating client-side makes "signals sent" equal "rotations performed."
- **No benefit to spamming.** The coalescing floor and the physical cost of building a
  multi-hop circuit mean faster signals produce zero additional exit diversity. The only
  outputs of hammering are wasted control-port chatter and a misleading record.
- **Fail loud, not silent.** A throttled `rotate` returns non-zero with an explicit
  message, so a caller learns it asked for something impossible — instead of getting a
  cheerful `250 OK` that hides the no-op.

The floor lives in one constant (`TOR_ROTATE_MIN_INTERVAL`), so if Tor's behavior ever
changes it is a one-line adjustment.

## The DNS-leak gotcha (the headline insight)

Rotating circuits does **nothing** if your client resolves DNS outside the tunnel:

```bash
curl --socks5 127.0.0.1:9050 https://example.com/          # LEAKS: client resolves DNS locally
curl --socks5-hostname 127.0.0.1:9050 https://example.com/ # SAFE: Tor resolves inside the tunnel
```

`--socks5` makes curl call `getaddrinfo()` locally and fire a plaintext port-53 query to
your system resolver *before* the tunnel is used — leaking which host you are visiting to
your ISP. `--socks5-hostname` (equivalently the `socks5h://` scheme) hands the raw
hostname to Tor and lets Tor resolve it. One letter — `socks5` vs `socks5h` — is the
entire bug. `torsocks <program>` is the safer wrapper for programs you do not fully
control because it fails closed.

Full explanation, verification method, and the `.onion` case:
[`docs/socks5-dns-leak.md`](docs/socks5-dns-leak.md).

## Usage

### Prerequisites

Enable the Tor control port with authentication. A sample config is in
[`examples/torrc-snippet`](examples/torrc-snippet):

```
ControlPort 9051
CookieAuthentication 1
```

Reload Tor after editing torrc.

### Configuration (environment)

| Variable | Default | Purpose |
|----------|---------|---------|
| `TOR_CONTROL_HOST` | `127.0.0.1` | control-port host |
| `TOR_CONTROL_PORT` | `9051` | control-port port |
| `TOR_CONTROL_PASSWD` | *(unset)* | control password (`HashedControlPassword` auth) |
| `TOR_COOKIE_PATH` | *(auto)* | path to `control_auth_cookie` (cookie auth) |
| `TOR_ROTATE_MIN_INTERVAL` | `10` | client-side floor between NEWNYM signals (seconds) |
| `TOR_ROTATE_DEFAULT_PERIOD` | `30` | default loop period for `rotaton` |

If neither a password nor a cookie path is set, the script auto-detects the cookie at the
usual locations and falls back to null auth only if the control port has none configured.

### As a CLI

```bash
./tor-rotate.sh rotate        # one new circuit now
./tor-rotate.sh on 45         # rotate every 45s in the background
./tor-rotate.sh off           # stop
```

### Sourced into your shell

```bash
source tor-rotate.sh
rotate
rotaton 45
rotatoff
```

### Verify it worked (without leaking DNS)

```bash
torsocks curl https://check.torproject.org/    # confirm you exit via Tor
# and watch port 53 to confirm DNS did NOT go out locally — see docs/socks5-dns-leak.md
```

## Repo layout

```
tor-rotate/
├── README.md
├── tor-rotate.sh
├── LICENSE
├── .gitignore
├── docs/
│   ├── newnym-rate-limit.md
│   └── socks5-dns-leak.md
└── examples/
    └── torrc-snippet
```

## License

MIT — see [LICENSE](LICENSE).

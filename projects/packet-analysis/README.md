# packet-analysis

Wireshark/tshark analysis demonstrating a DNS leak in SOCKS5 proxy usage: a client
configured with `curl --socks5` (and any app that speaks SOCKS5 the same way) resolves
hostnames *locally*, so every DNS query leaves the machine in cleartext on udp/53 to the
ISP resolver — even though the payload traffic itself goes through the proxy. Switching
to `curl --socks5-hostname` (or `socks5h://`, or `torsocks`) pushes name resolution
through the tunnel, and the cleartext DNS disappears from the wire. This repo contains
the annotated before/after analysis and the exact capture method.

**Status: in progress (captures pending)** — the writeups and method are complete; the
sanitized lab pcaps in `captures/` still need to be taken on the lab setup (see
`captures/README.md`).

## The finding

SOCKS5 (RFC 1928) supports two address types in the CONNECT request: a raw IPv4/IPv6
address, or a domain name (ATYP `0x03`) that the *proxy* resolves. Whether your DNS
leaks depends entirely on which one the client sends:

| Client invocation          | Who resolves the name | On the wire                                      |
|----------------------------|-----------------------|--------------------------------------------------|
| `curl --socks5 <proxy>`    | The local OS resolver | Cleartext udp/53 query to the ISP resolver, then proxied TCP |
| `curl --socks5-hostname <proxy>` | The proxy (e.g. Tor exit) | No cleartext DNS; hostname travels inside the SOCKS5 CONNECT |
| `torsocks <app>`           | Tor, via intercepted libc calls | No cleartext DNS                                 |

The leak defeats the point of the proxy for privacy purposes: an on-path observer (or
the resolver operator) sees every hostname you visit, timestamped, even though the
content connection is tunneled.

Full walkthrough with packet-level detail: [`docs/socks5-dns-leak.md`](docs/socks5-dns-leak.md)

## How to reproduce

Lab setup, capture commands, display filters, and pcap scrubbing procedure are in
[`docs/method.md`](docs/method.md). Short version:

```bash
# Terminal 1 — capture DNS and proxy traffic (lab machine, loopback proxy)
sudo tshark -i any -f "udp port 53 or tcp port 9050" -w socks5-test.pcapng

# Terminal 2 — leaking form
curl --socks5 127.0.0.1:9050 https://example.com/

# Terminal 2 — fixed form
curl --socks5-hostname 127.0.0.1:9050 https://example.com/

# Inspect: any DNS query for the target name is the leak
tshark -r socks5-test.pcapng -Y 'dns.qry.name contains "example"'
```

## Takeaway

"Using a SOCKS5 proxy" is not one behavior — the resolution side channel is decided by a
client flag, not by the proxy. When auditing a proxied or torified application, don't
read the config; capture the traffic and filter on `udp.port == 53`. If the target
hostname appears in a cleartext query, the tunnel is leaking metadata regardless of what
the application claims.

## Decisions

- **Capture on a lab/loopback setup, not live browsing.** The pcaps in this repo must be
  publishable. A capture taken during real browsing would embed real destinations, my
  own resolver, LAN addressing, and MAC addresses — sanitizing that after the
  fact is error-prone, and one missed field deanonymizes me. A dedicated lab
  capture against a documentation hostname contains nothing sensitive by construction,
  and it isolates exactly the packets that matter, keeping the pcaps tiny.
- **tshark over the Wireshark GUI for the method.** Every step is a copy-pasteable
  command, so the reproduction is scriptable and reviewable — a reader can verify the
  claim in two minutes without clicking through a GUI.
- **No fabricated captures.** Until the lab pcaps are taken, `captures/` holds only a
  README. The docs describe what the packets look like and include a clearly-labeled
  *illustrative* summary, but no synthetic data is presented as a real capture.

## Repo layout

```
packet-analysis/
├── README.md
├── captures/                 # sanitized lab pcaps (pending — see captures/README.md)
├── docs/
│   ├── socks5-dns-leak.md    # annotated walkthrough of the finding
│   └── method.md             # exact capture + scrub procedure
├── LICENSE
└── .gitignore
```

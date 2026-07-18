# Capture method

The exact, reproducible procedure for capturing the SOCKS5 DNS leak and its fix, and for
scrubbing the resulting pcaps down to small, publishable samples.

All example addresses are RFC 5737 documentation ranges (`192.0.2.0/24`,
`198.51.100.0/24`, `203.0.113.0/24`); the proxy is on loopback (`127.0.0.1:9050`, Tor's
default `SocksPort`). Nothing here is captured from a real network.

## Principles

- **Lab/loopback only.** Capture on a dedicated lab machine against a documentation
  hostname, never during real browsing. This keeps the pcap free of real destinations,
  resolver, LAN addressing, and MACs *by construction* rather than by after-the-fact
  scrubbing.
- **Isolate the packets that matter.** A tight capture filter plus a short fetch yields
  a handful of packets, so the committed pcap stays tiny and readable.
- **Control the resolver cache.** A missing DNS query can mean "resolved through the
  tunnel," "answered from cache," or "the fetch never happened." Flush the cache and
  confirm the fetch to make silence on udp/53 meaningful.

## 1. Prepare

```bash
# A SOCKS5 proxy on loopback. Tor's default SocksPort is 9050.
# (Any SOCKS5 proxy works for demonstrating the client-side resolution behavior.)

# Flush the local DNS cache so the "before" capture actually emits a query.
# Pick the one that matches the resolver in use, e.g.:
sudo resolvectl flush-caches      # systemd-resolved
# sudo systemctl restart nscd     # nscd
```

## 2. Capture

Use a **capture filter** (BPF, `-f`) to keep only DNS and the proxy port, so the file is
small:

```bash
# Terminal 1 — narrow capture on the lab host
sudo tshark -i any -f "udp port 53 or tcp port 9050" -w socks5-test.pcapng
```

```bash
# Terminal 2 — the leaking form: local resolution (ATYP 0x01)
curl --socks5 127.0.0.1:9050 https://example.com/

# Terminal 2 — the fixed form: proxy-side resolution (ATYP 0x03)
curl --socks5-hostname 127.0.0.1:9050 https://example.com/

# Equivalent fix via torsocks (LD_PRELOAD shim forces resolution through Tor):
torsocks curl https://example.com/
```

Capture the leaking and fixed forms into **separate files** (e.g. `socks5-leak.pcapng`
and `socks5-fixed.pcapng`) so the before/after comparison is clean. Stop each capture
(Ctrl-C on the tshark process) as soon as the fetch returns — you want seconds of
traffic, not a session.

## 3. Read / display filters

Display filters (`-Y`, Wireshark syntax) select what to look at after capture:

```bash
# Any DNS query for the target name — presence here is the leak
tshark -r socks5-leak.pcapng -Y 'dns.qry.name contains "example"'

# All DNS traffic (both directions)
tshark -r socks5-leak.pcapng -Y 'udp.port == 53'
# or simply:
tshark -r socks5-leak.pcapng -Y 'dns'

# The SOCKS5 CONNECT request — see the ATYP and, in the fixed form, the hostname
tshark -r socks5-fixed.pcapng -Y 'socks'
tshark -r socks5-fixed.pcapng -Y 'socks.remote_name'   # hostname inside the tunnel side
```

Pass/fail reduces to one filter over one capture:

- Query for the target hostname present → **leaking**.
- No query for the target hostname, and the fetch demonstrably succeeded → **fixed**.

Confirm the fetch actually happened (so silence isn't just "no request"): check curl's
exit status / output, or capture without the port filter once to see the connection.

## 4. Scrub and truncate before committing

Even a lab capture should be trimmed to the minimum and checked. Options:

```bash
# Keep only the first N packets (a leak needs only a few)
editcap -r socks5-leak.pcapng socks5-leak-small.pcapng 1-8

# Or keep only packets matching a display filter, dropping everything else
tshark -r socks5-leak.pcapng -Y 'dns or socks' -w socks5-leak-min.pcapng

# Optionally rewrite/anonymize IPs and MACs to fixed values as a belt-and-braces step
# (map real addresses to documentation ranges; -m also scrambles MAC OUIs)
tracewrangler   # GUI, or:
bittwiste -I in.pcap -O out.pcap -T ip -s 192.0.2.10 -d 198.51.100.53   # example
```

Then run the sanitization scan and eyeball the packets before committing:

```bash
# Human-readable dump to review every field for anything real
tshark -r socks5-leak-min.pcapng -V | less

# Confirm no real addressing/MACs slipped through (expect only loopback / RFC 5737)
tshark -r socks5-leak-min.pcapng -Y 'eth.addr or ip.addr' -T fields \
  -e ip.src -e ip.dst -e eth.src -e eth.dst | sort -u
```

Checklist before a pcap enters `captures/`:

- Addresses are loopback or RFC 5737 documentation ranges only.
- No real SSIDs, credentials, hostnames, or tailnet CGNAT-range addresses.
- No real MAC addresses.
- File is a handful of packets, not a session.

> OPERATOR: run this procedure on your lab setup, produce the two small pcaps, verify
> them against the checklist, then commit them with `git add -f` (the repo `.gitignore`
> excludes `*.pcap*` by default).

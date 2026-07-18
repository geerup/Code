# The SOCKS5 DNS leak: `--socks5` vs `--socks5-hostname`

An annotated walkthrough of why a "fully proxied" client can still broadcast every
hostname it visits in cleartext, what that looks like on the wire, and how the fixed
configuration differs packet-by-packet.

All addresses in this document are RFC 5737 documentation addresses (`192.0.2.0/24`,
`198.51.100.0/24`, `203.0.113.0/24`) and the proxy is assumed on loopback
(`127.0.0.1:9050`, Tor's default SocksPort). No values here come from a real network.

## 1. Where the leak comes from

SOCKS5 (RFC 1928) defines the CONNECT request as:

```
+----+-----+-------+------+----------+----------+
|VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
+----+-----+-------+------+----------+----------+
```

`ATYP` is the pivot point:

- `0x01` — DST.ADDR is a 4-byte IPv4 address. To produce this, **the client must have
  already resolved the hostname itself**, using the ordinary OS resolver path
  (`getaddrinfo()` → `/etc/resolv.conf` → udp/53 to the configured resolver).
- `0x03` — DST.ADDR is a length-prefixed domain name. **The proxy resolves it** on the
  far side of the tunnel. For Tor, that means the exit relay resolves it; the client
  machine never emits a DNS query for the name.
- `0x04` — 16-byte IPv6, same local-resolution implication as `0x01`.

`curl --socks5 <proxy>` uses ATYP `0x01`: curl calls the resolver first, then hands the
resulting IP to the proxy. `curl --socks5-hostname <proxy>` (equivalently a
`socks5h://` proxy URL) uses ATYP `0x03` and sends the name itself.

This is not a curl quirk. Any SOCKS5-capable application faces the same choice, and
many default to local resolution or expose it as an obscure setting (Firefox's
`network.proxy.socks_remote_dns`, Python `requests` needing `socks5h://` rather than
`socks5://`, etc.). `torsocks` avoids the problem a third way: it LD_PRELOADs wrappers
around the libc resolver calls so even a naive application's lookups are forced through
Tor.

## 2. What the leak looks like on the wire (before)

Running the leaking form on the lab host while capturing:

```bash
curl --socks5 127.0.0.1:9050 https://example.com/
```

Three things appear in the capture, in order:

1. **A cleartext DNS query on udp/53** from the lab host to its configured resolver —
   in a home setting, the ISP's resolver. It is a standard query, `A` record (usually
   paired with an `AAAA`), with the full target hostname in the QNAME field, readable by
   anyone on the path. Filter: `udp.port == 53` or just `dns`.
2. **The DNS response** carrying the resolved address back in the answer section.
3. **A TCP connection to the proxy** (loopback 9050) whose SOCKS5 CONNECT request
   contains ATYP `0x01` and the *IP address* obtained in step 2 — the hostname never
   appears in the proxy stream, because the damage was already done in step 1.

Illustrative summary of the relevant packets — **this is a hypothetical rendering of
the expected capture, using documentation addresses, not a real capture** (real,
sanitized pcaps are pending in `captures/`):

```
# ILLUSTRATIVE — not captured data
No.  Source          Destination     Proto  Info
1    192.0.2.10      198.51.100.53   DNS    Standard query A example.com
2    198.51.100.53   192.0.2.10      DNS    Standard query response A 203.0.113.80
3    127.0.0.1       127.0.0.1       TCP    52310 → 9050 [SYN]
4    127.0.0.1       127.0.0.1       SOCKS  Connect to server request (IPv4: 203.0.113.80)
...
```

Here `192.0.2.10` stands in for the lab host and `198.51.100.53` for the upstream
resolver. Packet 1 is the leak: the observer learns the hostname, the client that asked
for it, and when.

## 3. What the fix looks like on the wire (after)

```bash
curl --socks5-hostname 127.0.0.1:9050 https://example.com/
```

With the same capture running:

- **No packet matches `udp.port == 53`** for the target name. This absence is the
  entire finding — the "after" evidence is a filter that returns nothing.
- The SOCKS5 CONNECT on loopback now carries ATYP `0x03` with the domain string inside
  it. On a loopback capture you can see the hostname inside the SOCKS5 request
  (`socks.remote_name` in Wireshark) — which is fine, because that byte string never
  leaves the machine except wrapped in the tunnel's encryption.
- Everything external is the tunnel traffic itself (for Tor, TLS to the guard relay).
  An on-path observer sees that you are using Tor, but not which name you resolved.

The same negative result holds for `torsocks curl https://example.com/`: the LD_PRELOAD
shim converts the resolver call into a Tor-side resolution, so udp/53 stays silent.

## 4. Verifying it yourself

The pass/fail test reduces to one filter over one capture (full procedure in
[`method.md`](method.md)):

```bash
tshark -r socks5-test.pcapng -Y 'dns.qry.name contains "example"'
```

- Output contains a query for the target hostname → **leaking**.
- No output for the target hostname (while the fetch demonstrably succeeded) → **fixed**.

Note the control matters: a lookup can be absent because resolution went through the
tunnel, or because the answer was cached, or because the fetch never happened. The
method doc includes flushing/avoiding the local cache and confirming the HTTP fetch
succeeded, so silence on udp/53 actually means what it appears to mean.

## 5. Why this matters (SOC framing)

- **For defenders:** cleartext DNS adjacent to proxy/VPN/Tor traffic is a high-signal
  detection artifact. A host emitting udp/53 queries for external names *and* sustained
  traffic to a known proxy/tunnel endpoint is a misconfigured evader — the DNS log hands
  you their browsing intent even though the sessions themselves are opaque.
- **For anyone deploying a proxy:** the client flag, not the proxy, decides whether DNS
  leaks. Validation must happen at the packet level. "It works" (pages load) is
  indistinguishable from "it leaks" without a capture.
- **The general lesson:** metadata channels (DNS, SNI, traffic timing) routinely
  outlive the encryption of the primary channel. Auditing a privacy control means
  enumerating side channels, not confirming the main channel is encrypted.

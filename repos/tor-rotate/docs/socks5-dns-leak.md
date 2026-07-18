# The SOCKS5 DNS leak: `--socks5` vs `--socks5-hostname`

This is the headline insight of the repo. Rotating Tor circuits is pointless if your
client resolves hostnames **outside** the tunnel, because the DNS query alone
deanonymizes what you are doing to whoever can see your resolver traffic.

## The footgun

SOCKS5 supports two ways of handing a destination to the proxy:

- **Send an IP address.** The client resolves the hostname to an IP *itself*, then asks
  the proxy to connect to that IP.
- **Send a hostname.** The client passes the raw hostname to the proxy and lets the
  **proxy** resolve it.

Most tools default to the first behavior, or make it easy to select. In curl:

| Flag | Who resolves DNS | Leaks? |
|------|------------------|--------|
| `--socks5 127.0.0.1:9050` | **the local client** | **YES** — DNS goes to your system resolver, in the clear |
| `--socks5-hostname 127.0.0.1:9050` | **Tor (the proxy)** | No — hostname is resolved inside the Tor network |

With `--socks5`, curl calls `getaddrinfo()` locally *before* it ever talks to Tor. That
lookup goes to whatever resolver your OS is configured for — your ISP, your router, a
public resolver — as a **plaintext UDP query on port 53**. Your traffic to the site then
rides the Tor tunnel, but you have already broadcast *which site* to a third party. An
observer correlating the DNS query timestamp with the subsequent Tor connection can
reconstruct your activity. For a SOC or threat-intel context, this is the difference
between "we see encrypted Tor traffic" and "we see this host looked up `example.onion`'s
front domain three seconds before the circuit opened."

`.onion` addresses make the failure even louder: your system resolver cannot resolve
`.onion` at all, so with `--socks5` the request either fails or, on some configurations,
leaks the `.onion` name to an upstream resolver that logs the NXDOMAIN. Either way the
name has left the machine.

## The fix

**Always resolve through the proxy.** Two reliable ways:

### 1. Use the hostname-resolving flag

```bash
# WRONG — leaks DNS to your system resolver
curl --socks5 127.0.0.1:9050 https://check.torproject.org/

# RIGHT — Tor resolves the hostname inside the tunnel
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/
```

The rule generalizes: whenever a tool offers a "socks5" vs "socks5h" scheme, pick the one
that resolves remotely. In URL form that is the **`socks5h://`** scheme:

```bash
curl --proxy socks5h://127.0.0.1:9050 https://check.torproject.org/
export ALL_PROXY=socks5h://127.0.0.1:9050   # note the 'h'
```

`socks5://` (no `h`) resolves locally and leaks; `socks5h://` resolves at the proxy.
One letter is the entire bug.

### 2. Use `torsocks`

`torsocks` wraps a program and intercepts its network calls, forcing name resolution
through Tor and blocking any traffic that would bypass the proxy (including stray UDP and
direct-IP connections that a plain SOCKS wrapper would let through):

```bash
torsocks curl https://check.torproject.org/
```

`torsocks` is the safer default for programs you do not fully control, because it fails
closed: connections it cannot route over Tor are blocked rather than silently leaked.

## How to verify you are not leaking

- **`check.torproject.org`** confirms your HTTP path exits via Tor, but it does **not**
  prove your DNS went through Tor. Do not treat a green check page as proof of no DNS
  leak.
- Watch your own resolver traffic while making a request. On a lab/loopback setup:

  ```bash
  # In one terminal, capture DNS. In another, make the request.
  sudo tcpdump -n -i any port 53
  curl --socks5 127.0.0.1:9050 https://example.com/        # you WILL see a port-53 query
  curl --socks5-hostname 127.0.0.1:9050 https://example.com/   # you will NOT
  ```

  The presence or absence of that port-53 query is the whole finding. (See the companion
  `packet-analysis` repo for an annotated capture of both cases.)

## Takeaway

Circuit rotation protects the *path*; it does nothing for the *name resolution*. If DNS
happens on the client, every rotation in the world still leaves a plaintext trail of what
you looked up. Resolve at the proxy — `--socks5-hostname` / `socks5h://` / `torsocks` —
or the tunnel is decorative.

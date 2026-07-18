# captures/

Sanitized lab packet captures demonstrating the SOCKS5 DNS leak and the fix.

**Status: pending.** No pcaps are committed yet. They must be captured by the operator
on a lab/loopback setup — see [`../docs/method.md`](../docs/method.md) for the exact
procedure — and then reviewed before they land here.

## What goes here (once captured)

Two tiny captures, taken against a documentation hostname on a lab machine:

- `socks5-leak.pcapng` — the leaking form (`curl --socks5 ...`): a cleartext DNS query
  for the target name on udp/53 is present.
- `socks5-fixed.pcapng` — the fixed form (`curl --socks5-hostname ...` or `torsocks`):
  no cleartext DNS query for the target name.

## Rules for anything committed here

- **Real captures only — never fabricated.** Do not commit synthetic pcaps or hex dumps
  presented as real captures. If it wasn't captured off a wire/loopback, it does not go
  here. Illustrative, clearly-labeled packet summaries live in the docs, not as pcap
  files here.
- **Lab/loopback capture, not live browsing.** Capture on a dedicated lab setup against
  a documentation hostname so the pcap contains nothing sensitive by construction.
- **Tiny.** Trim to just the packets that make the point (a handful, not a session).
  See the truncation/slicing steps in `method.md`.
- **Sanitized and verified.** Before committing, confirm the capture contains no real
  SSIDs, credentials, LAN addressing, MAC addresses, tailnet CGNAT-range
  addresses, or real external destinations. Prefer captures where addressing is loopback
  or RFC 5737 documentation ranges.

> OPERATOR: capture both pcaps per `docs/method.md`, run the sanitization scan over
> them, and commit them here with `git add -f` (the repo `.gitignore` excludes `*.pcap*`
> by default so nothing is committed by accident).

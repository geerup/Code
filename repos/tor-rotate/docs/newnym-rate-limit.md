# NEWNYM rate limiting: why fast rotation loops are a lie

## The signal

The Tor control protocol exposes `SIGNAL NEWNYM`. It tells the Tor client to stop
using existing circuits for **new** connections, so subsequent streams get built over
fresh circuits (and therefore, usually, fresh exit relays). It is the mechanism behind
"give me a new identity" in Tor Browser and behind any circuit-rotation script.

## The coalescing window

`NEWNYM` is **not** free and it is **not** instantaneous. Tor deliberately rate-limits
it. Internally, Tor tracks the time of the last new-identity event and enforces a
minimum spacing (`MAX_SIGNAL_NEWNYM_RATE`, 10 seconds in the C-Tor source). If a second
`NEWNYM` arrives inside that window, Tor does not queue a second rotation and it does not
rotate twice — it **coalesces** the request: the signal is folded into the pending one,
and you get a single effective rotation for the burst.

The control port still answers `250 OK` to every `NEWNYM` you send. That `250` means
"signal received and understood," **not** "a new circuit set was just built for you."
This is the trap: the reply looks identical whether Tor acted on the signal or absorbed
it into the coalescing window.

There is a second, physical reason spamming does nothing: building a fresh circuit
involves a multi-hop TLS handshake and path selection across the network. It takes on the
order of seconds. Even if Tor honored every signal, the circuits could not be rebuilt
faster than the network allows.

## What this means for a naive loop

A loop like:

```bash
while true; do
    printf 'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT\r\n' | nc 127.0.0.1 9051
    sleep 1        # <-- rotate "every second"
done
```

*feels* like it rotates once per second. It does not. It sends 10 signals per effective
rotation, all but one of which are coalesced away. The operator reads the stream of
`250 OK` replies and believes they are cycling through ten exit relays; in reality they
are on roughly the same circuit for ~10 seconds at a time. Worse, the false sense of
churn can lead someone to believe correlation is harder than it actually is.

Sending faster than the window buys you three things, all bad:

1. **No extra anonymity.** You do not get more distinct exits than the ~10s cadence
   allows.
2. **Wasted control-port chatter** and, in poorly written loops, connection churn that
   is itself a fingerprint on the local host.
3. **A misleading log.** Every `250 OK` reads as a success, hiding the fact that most
   were no-ops.

## The fix this repo implements: gate on the client side

`tor-rotate.sh` refuses to send a `NEWNYM` if fewer than `TOR_ROTATE_MIN_INTERVAL`
seconds (default **10**) have passed since the last one it actually sent. It records the
timestamp of each accepted signal in a small state file and compares against it before
every send:

- One-shot `rotate` prints an explicit `throttled` message and exits non-zero if you
  call it inside the window, instead of pretending to have rotated.
- `rotaton [SECS]` clamps any period below the floor up to the floor, because a smaller
  period would only generate coalesced no-ops.

Gating on the client means the number of signals you send equals the number of rotations
Tor will actually honor. The log tells the truth, and the loop can never out-run the
network.

## Notes

- The 10-second figure is the default in mainline Tor. It is a compiled constant, not a
  torrc option, so you should treat 10s as the floor regardless of your configuration.
- `NEWNYM` affects **new** streams only. Long-lived connections already open on the old
  circuit keep using it until they close. Rotation is not retroactive.
- Getting a "new identity" is best-effort at the path level: Tor avoids reusing the same
  circuits, but exit-relay diversity is bounded by the consensus and your path
  constraints. A new circuit is not guaranteed to be a new exit country or ASN.

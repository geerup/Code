#!/usr/bin/env bash
#
# tor-rotate.sh — Tor circuit rotation helpers with client-side NEWNYM rate limiting.
#
# Provides:
#   rotate            one-shot: request a new circuit now (rate-limited)
#   rotaton [SECS]    start a background loop that rotates every SECS (default 30)
#   rotatoff          stop the background loop
#
# Usable two ways:
#   1. Source it to get the functions in your shell:
#        source tor-rotate.sh
#        rotaton 45
#        rotatoff
#   2. Run it as a CLI:
#        ./tor-rotate.sh rotate
#        ./tor-rotate.sh on 45
#        ./tor-rotate.sh off
#
# Control-port auth is read from the environment (placeholders only — set your own):
#   TOR_CONTROL_HOST   default 127.0.0.1
#   TOR_CONTROL_PORT   default 9051
#   TOR_CONTROL_PASSWD control-port password (HashedControlPassword auth). Optional.
#   TOR_COOKIE_PATH    path to the control_auth_cookie (CookieAuthentication). Optional.
#
# If neither TOR_CONTROL_PASSWD nor TOR_COOKIE_PATH is set, the script tries cookie
# auth at the default Tor cookie location, then falls back to a null AUTHENTICATE
# (only works if the control port has no auth configured — not recommended).
#
# NEWNYM RATE LIMIT: Tor coalesces NEWNYM signals that arrive within its
# NewCircuitPeriod window (~10s by default). Sending faster gains you nothing but
# looks like you rotated. This script enforces a client-side minimum interval so a
# loop can never out-run what Tor will actually honor. See docs/newnym-rate-limit.md.
#
# DNS LEAK WARNING: rotating circuits does nothing for anonymity if your client
# resolves DNS outside the tunnel. Use --socks5-hostname (not --socks5) or torsocks.
# See docs/socks5-dns-leak.md.

# --- configuration -----------------------------------------------------------

# Minimum seconds between NEWNYM signals actually sent to Tor. Tor coalesces
# anything faster than its NewCircuitPeriod (~10s), so 10 is the sane floor.
TOR_ROTATE_MIN_INTERVAL="${TOR_ROTATE_MIN_INTERVAL:-10}"

# Default loop period when rotaton is called without an argument.
TOR_ROTATE_DEFAULT_PERIOD="${TOR_ROTATE_DEFAULT_PERIOD:-30}"

# Where loop state is kept (PID file + last-signal timestamp).
TOR_ROTATE_RUNDIR="${TOR_ROTATE_RUNDIR:-${TMPDIR:-/tmp}/tor-rotate-$(id -u)}"

# --- internals ---------------------------------------------------------------

_tor_rotate_host() { printf '%s' "${TOR_CONTROL_HOST:-127.0.0.1}"; }
_tor_rotate_port() { printf '%s' "${TOR_CONTROL_PORT:-9051}"; }

# Resolve the control cookie path: explicit env, else common defaults.
_tor_rotate_cookie_path() {
    if [ -n "${TOR_COOKIE_PATH:-}" ]; then
        printf '%s' "$TOR_COOKIE_PATH"
        return 0
    fi
    local candidate
    for candidate in \
        /run/tor/control.authcookie \
        /var/run/tor/control.authcookie \
        /var/lib/tor/control_auth_cookie; do
        if [ -r "$candidate" ]; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

# Build the AUTHENTICATE line for the control protocol.
# Password auth uses a quoted string; cookie auth uses the hex-encoded cookie bytes.
_tor_rotate_auth_line() {
    if [ -n "${TOR_CONTROL_PASSWD:-}" ]; then
        printf 'AUTHENTICATE "%s"' "$TOR_CONTROL_PASSWD"
        return 0
    fi
    local cookie
    if cookie="$(_tor_rotate_cookie_path)"; then
        local hex
        # xxd if present, else od — emit the cookie as a lowercase hex string.
        if command -v xxd >/dev/null 2>&1; then
            hex="$(xxd -p -c 256 "$cookie" | tr -d '\n')"
        else
            hex="$(od -An -tx1 -v "$cookie" | tr -d ' \n')"
        fi
        printf 'AUTHENTICATE %s' "$hex"
        return 0
    fi
    # No credentials available: attempt null auth (works only if no auth configured).
    printf 'AUTHENTICATE'
    return 0
}

# Send raw control-port commands and print the reply.
# Prefers a bash /dev/tcp connection; falls back to nc if available.
_tor_rotate_send() {
    local payload="$1"
    local host port
    host="$(_tor_rotate_host)"
    port="$(_tor_rotate_port)"

    if command -v nc >/dev/null 2>&1; then
        printf '%b' "$payload" | nc -w 3 "$host" "$port"
        return $?
    fi

    # Pure-bash TCP. Subshell so the fd redirection is scoped.
    (
        exec 3<>"/dev/tcp/${host}/${port}" || return 1
        printf '%b' "$payload" >&3
        # Read whatever the control port sends back within a short window.
        while IFS= read -r -t 3 line <&3; do
            printf '%s\n' "$line"
        done
        exec 3<&- 3>&-
    )
}

# Issue AUTHENTICATE + SIGNAL NEWNYM + QUIT in one control session.
_tor_rotate_newnym() {
    local auth reply
    auth="$(_tor_rotate_auth_line)"
    reply="$(_tor_rotate_send "${auth}\r\nSIGNAL NEWNYM\r\nQUIT\r\n")"

    if printf '%s' "$reply" | grep -q '^250'; then
        return 0
    fi
    printf 'tor-rotate: control port did not accept the request:\n%s\n' "$reply" >&2
    return 1
}

_tor_rotate_now_epoch() { date +%s; }

# Enforce the client-side minimum interval. Returns 0 if a signal may be sent,
# 1 (with a message) if we are still inside the coalescing window.
_tor_rotate_gate() {
    mkdir -p "$TOR_ROTATE_RUNDIR" 2>/dev/null
    local stamp_file="${TOR_ROTATE_RUNDIR}/last-newnym"
    local now last delta
    now="$(_tor_rotate_now_epoch)"
    last=0
    if [ -r "$stamp_file" ]; then
        last="$(cat "$stamp_file" 2>/dev/null)"
        case "$last" in
            ''|*[!0-9]*) last=0 ;;
        esac
    fi
    delta=$(( now - last ))
    if [ "$delta" -lt "$TOR_ROTATE_MIN_INTERVAL" ]; then
        printf 'tor-rotate: throttled — %ss since last NEWNYM, minimum is %ss (Tor coalesces faster signals).\n' \
            "$delta" "$TOR_ROTATE_MIN_INTERVAL" >&2
        return 1
    fi
    printf '%s' "$now" >"$stamp_file"
    return 0
}

# --- public API --------------------------------------------------------------

# One-shot rotation, rate-limited.
rotate() {
    if ! _tor_rotate_gate; then
        return 1
    fi
    if _tor_rotate_newnym; then
        printf 'tor-rotate: requested new circuit (NEWNYM) at %s\n' "$(date '+%H:%M:%S')"
        return 0
    fi
    return 1
}

# Background loop: rotate every PERIOD seconds (>= the coalescing floor).
rotaton() {
    local period="${1:-$TOR_ROTATE_DEFAULT_PERIOD}"
    case "$period" in
        ''|*[!0-9]*)
            printf 'tor-rotate: rotaton needs a positive integer period (seconds).\n' >&2
            return 1
            ;;
    esac
    if [ "$period" -lt "$TOR_ROTATE_MIN_INTERVAL" ]; then
        printf 'tor-rotate: period %ss is below the %ss floor; clamping (Tor would coalesce anyway).\n' \
            "$period" "$TOR_ROTATE_MIN_INTERVAL" >&2
        period="$TOR_ROTATE_MIN_INTERVAL"
    fi

    mkdir -p "$TOR_ROTATE_RUNDIR" 2>/dev/null
    local pid_file="${TOR_ROTATE_RUNDIR}/loop.pid"

    if [ -r "$pid_file" ]; then
        local existing
        existing="$(cat "$pid_file" 2>/dev/null)"
        if [ -n "$existing" ] && kill -0 "$existing" 2>/dev/null; then
            printf 'tor-rotate: a rotation loop is already running (pid %s). Run rotatoff first.\n' "$existing" >&2
            return 1
        fi
    fi

    # Launch the loop in the background.
    (
        while true; do
            rotate
            sleep "$period"
        done
    ) &
    local loop_pid=$!
    printf '%s' "$loop_pid" >"$pid_file"
    printf 'tor-rotate: rotation loop started (pid %s, every %ss).\n' "$loop_pid" "$period"
    return 0
}

# Stop the background loop.
rotatoff() {
    local pid_file="${TOR_ROTATE_RUNDIR}/loop.pid"
    if [ ! -r "$pid_file" ]; then
        printf 'tor-rotate: no rotation loop recorded.\n' >&2
        return 1
    fi
    local loop_pid
    loop_pid="$(cat "$pid_file" 2>/dev/null)"
    if [ -n "$loop_pid" ] && kill -0 "$loop_pid" 2>/dev/null; then
        kill "$loop_pid" 2>/dev/null
        printf 'tor-rotate: rotation loop stopped (pid %s).\n' "$loop_pid"
    else
        printf 'tor-rotate: recorded loop (pid %s) was not running.\n' "${loop_pid:-?}" >&2
    fi
    rm -f "$pid_file"
    return 0
}

# --- CLI dispatch ------------------------------------------------------------
# Only runs when executed directly, not when sourced.

_tor_rotate_usage() {
    cat >&2 <<'EOF'
Usage: tor-rotate.sh <command> [args]

Commands:
  rotate            Request a new circuit now (rate-limited).
  on [SECONDS]      Start a rotation loop (default 30s, floor 10s).
  off               Stop the rotation loop.

Environment:
  TOR_CONTROL_HOST     default 127.0.0.1
  TOR_CONTROL_PORT     default 9051
  TOR_CONTROL_PASSWD   control-port password (optional)
  TOR_COOKIE_PATH      path to control_auth_cookie (optional)

See docs/newnym-rate-limit.md and docs/socks5-dns-leak.md.
EOF
}

# Detect "sourced vs executed" in a bash-portable way.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    case "${1:-}" in
        rotate)     shift; rotate "$@" ;;
        on|rotaton) shift; rotaton "$@" ;;
        off|rotatoff) shift; rotatoff "$@" ;;
        ''|-h|--help|help) _tor_rotate_usage; exit 1 ;;
        *)
            printf 'tor-rotate: unknown command "%s"\n' "$1" >&2
            _tor_rotate_usage
            exit 1
            ;;
    esac
fi

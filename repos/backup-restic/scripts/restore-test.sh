#!/usr/bin/env bash
#
# restore-test.sh — prove the backups are restorable, not just present.
#
# What it does:
#   1. Restores the latest snapshot into a scratch directory.
#   2. Builds a SHA-256 manifest of every restored file.
#   3. Compares each restored file's checksum against the live source file.
#   4. Prints a summary: matched / drifted / missing-from-live.
#   5. Cleans up the scratch directory.
#
# Interpretation:
#   - "matched"  : restored file is byte-identical to the live file. Good.
#   - "drifted"  : live file changed since the snapshot was taken. Expected
#                  for active files (logs, databases); investigate only if
#                  files you know are static show up here.
#   - "missing"  : file exists in the snapshot but not on the live system
#                  (deleted since the snapshot). Informational.
#   The test FAILS (non-zero exit) only if the restore itself fails or
#   restores zero files — checksum drift alone is not a failure.
#
# Run this on a schedule (monthly) or at minimum after any change to the
# backup configuration, and record the run in docs/restore-runbook.md.
#
# Exit codes:
#   0  restore succeeded and files were verified
#   1  configuration error
#   3  restore failed or produced no files

set -euo pipefail

# --- configuration ----------------------------------------------------------

CONFIG_FILE="${RESTIC_BACKUP_CONFIG:-/etc/restic-backup/restic.env}"

if [[ ! -r "${CONFIG_FILE}" ]]; then
    echo "ERROR: config file not readable: ${CONFIG_FILE}" >&2
    exit 1
fi

# shellcheck source=/dev/null
set -a
source "${CONFIG_FILE}"
set +a

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY must be set in ${CONFIG_FILE}}"
: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE must be set in ${CONFIG_FILE}}"

# Optionally restrict the test to a subtree (faster on big repos):
#   RESTORE_TEST_INCLUDE=/etc ./restore-test.sh
RESTORE_TEST_INCLUDE="${RESTORE_TEST_INCLUDE:-}"

SCRATCH_DIR="$(mktemp -d /tmp/restic-restore-test.XXXXXX)"
cleanup() { rm -rf "${SCRATCH_DIR}"; }
trap cleanup EXIT

echo "=== restore test starting: $(date -Is) ==="
echo "repository:  ${RESTIC_REPOSITORY}"
echo "scratch dir: ${SCRATCH_DIR}"

# --- restore latest snapshot into scratch dir -------------------------------

restore_args=(restore latest --target "${SCRATCH_DIR}")
if [[ -n "${RESTORE_TEST_INCLUDE}" ]]; then
    restore_args+=(--include "${RESTORE_TEST_INCLUDE}")
    echo "include:     ${RESTORE_TEST_INCLUDE}"
fi

if ! restic "${restore_args[@]}"; then
    echo "FAIL: restic restore returned an error." >&2
    exit 3
fi

# --- checksum comparison -----------------------------------------------------

matched=0
drifted=0
missing=0
total=0

# Walk everything restic put in the scratch dir. Restored paths mirror the
# original absolute paths under ${SCRATCH_DIR}.
while IFS= read -r -d '' restored_file; do
    total=$((total + 1))
    live_file="${restored_file#"${SCRATCH_DIR}"}"

    if [[ ! -f "${live_file}" ]]; then
        missing=$((missing + 1))
        continue
    fi

    restored_sum="$(sha256sum "${restored_file}" | cut -d' ' -f1)"
    live_sum="$(sha256sum "${live_file}" | cut -d' ' -f1)"

    if [[ "${restored_sum}" == "${live_sum}" ]]; then
        matched=$((matched + 1))
    else
        drifted=$((drifted + 1))
        echo "DRIFT: ${live_file}"
    fi
done < <(find "${SCRATCH_DIR}" -type f -print0)

# --- summary ------------------------------------------------------------------

echo "=== restore test summary: $(date -Is) ==="
echo "files restored:        ${total}"
echo "checksums matched:     ${matched}"
echo "drifted since backup:  ${drifted}"
echo "missing from live fs:  ${missing}"

if [[ "${total}" -eq 0 ]]; then
    echo "FAIL: restore produced zero files — repository or snapshot problem." >&2
    exit 3
fi

echo "PASS: restore verified. Record this run (date + result) in docs/restore-runbook.md."

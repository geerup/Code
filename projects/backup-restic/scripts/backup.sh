#!/usr/bin/env bash
#
# backup.sh — restic backup with excludes, retention, and prune.
#
# Intended to be run by systemd (restic-backup.service), but works fine
# interactively for a first manual run.
#
# All configuration comes from an environment file (default:
# /etc/restic-backup/restic.env — see .env.example in this repo).
# Nothing secret lives in this script or in the unit files.
#
# Exit codes:
#   0  backup + forget/prune succeeded
#   1  configuration error (missing env file / required vars)
#   2  another instance already running
#   *  restic's own exit code on failure

set -euo pipefail

# --- configuration ----------------------------------------------------------

CONFIG_FILE="${RESTIC_BACKUP_CONFIG:-/etc/restic-backup/restic.env}"

if [[ ! -r "${CONFIG_FILE}" ]]; then
    echo "ERROR: config file not readable: ${CONFIG_FILE}" >&2
    echo "Copy .env.example there and fill in real values (chmod 600)." >&2
    exit 1
fi

# shellcheck source=/dev/null
set -a
source "${CONFIG_FILE}"
set +a

# Required variables — fail loudly rather than let restic guess.
: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY must be set in ${CONFIG_FILE}}"
: "${RESTIC_PASSWORD_FILE:?RESTIC_PASSWORD_FILE must be set in ${CONFIG_FILE}}"
: "${BACKUP_PATHS:?BACKUP_PATHS must be set in ${CONFIG_FILE} (space-separated list)}"

# Optional variables with defaults.
EXCLUDE_FILE="${EXCLUDE_FILE:-/etc/restic-backup/excludes.txt}"
KEEP_DAILY="${KEEP_DAILY:-7}"
KEEP_WEEKLY="${KEEP_WEEKLY:-4}"
KEEP_MONTHLY="${KEEP_MONTHLY:-6}"
BACKUP_TAG="${BACKUP_TAG:-scheduled}"
LOCK_FILE="${LOCK_FILE:-/run/restic-backup.lock}"

if [[ ! -r "${RESTIC_PASSWORD_FILE}" ]]; then
    echo "ERROR: RESTIC_PASSWORD_FILE not readable: ${RESTIC_PASSWORD_FILE}" >&2
    exit 1
fi

# --- single-instance lock ---------------------------------------------------
# The systemd timer should never overlap runs, but protect against a manual
# run colliding with a scheduled one.

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    echo "ERROR: another backup run holds ${LOCK_FILE}; exiting." >&2
    exit 2
fi

# --- build argument lists ---------------------------------------------------

# BACKUP_PATHS is a space-separated string in the env file; split it here.
# Paths with spaces are not supported by design — keep backup roots simple.
read -r -a backup_paths <<< "${BACKUP_PATHS}"

exclude_args=()
if [[ -r "${EXCLUDE_FILE}" ]]; then
    exclude_args+=(--exclude-file "${EXCLUDE_FILE}")
else
    echo "WARN: exclude file not found (${EXCLUDE_FILE}); backing up without excludes." >&2
fi

# --- run --------------------------------------------------------------------

echo "=== restic backup starting: $(date -Is) ==="
echo "repository: ${RESTIC_REPOSITORY}"
echo "paths:      ${backup_paths[*]}"

restic backup \
    --tag "${BACKUP_TAG}" \
    --one-file-system \
    --exclude-caches \
    "${exclude_args[@]}" \
    --verbose \
    "${backup_paths[@]}"

echo "=== applying retention policy: ${KEEP_DAILY}d/${KEEP_WEEKLY}w/${KEEP_MONTHLY}m ==="

restic forget \
    --tag "${BACKUP_TAG}" \
    --keep-daily "${KEEP_DAILY}" \
    --keep-weekly "${KEEP_WEEKLY}" \
    --keep-monthly "${KEEP_MONTHLY}" \
    --prune

echo "=== quick repository check ==="
# Structural check every run (cheap). Data verification is done separately by
# restore-test.sh, which actually restores files and compares checksums.
restic check

echo "=== restic backup finished: $(date -Is) ==="

# backup-restic

Automated [restic](https://restic.net/) backups driven by systemd timers, with a
**restore procedure that is meant to be run, not assumed**. A backup you have never
restored is a hypothesis; this repo turns it into something you have actually tested. It
covers the full loop: scheduled encrypted backups, a retention/prune policy, and a
`restore-test.sh` that restores the latest snapshot and checksums it against the live
filesystem.

**Status: in progress** — the backup script, restore-test script, and systemd units are
written and run. The restore runbook in `docs/restore-runbook.md` is a procedure the
operator must execute and date; no completed test log is claimed here yet.

## What it backs up and why tested restores matter

Backup roots, excludes, retention, and the repository backend all come from an
environment file (`/etc/restic-backup/restic.env`, modeled by `.env.example`) — nothing
host-specific or secret lives in the scripts or units. A typical set of roots is system
config (`/etc`), home directories, and service/compose data; you set `BACKUP_PATHS` to
match your host.

Tested restores matter because every backup system fails silently in the same way: the
job runs green for months, then the one time you need it the repository is corrupt, the
password is lost, the snapshot is empty, or the excludes quietly dropped the one directory
that mattered. The only way to know is to restore. `restore-test.sh` does exactly that —
restores the latest snapshot into a scratch dir and compares SHA-256 sums against the live
files — so "restorable" is a verified fact with a date, not an assumption. This is also the
question every interview asks: *when did you last test a restore?*

## Schedule

Backups run on a systemd timer (`systemd/restic-backup.timer`), daily with a randomized
delay so the run does not fire at a predictable instant:

```
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=1h
Persistent=true          # catch up a missed run after downtime
```

The timer starts `restic-backup.service` (a `Type=oneshot` unit) which runs
`scripts/backup.sh`. A `flock` in the script prevents a manual run from overlapping a
scheduled one.

## Retention / prune policy

After each backup the script applies a `restic forget --prune` policy (defaults, override
in the env file):

| Window  | Keep | Env var        |
|---------|------|----------------|
| Daily   | 7    | `KEEP_DAILY`   |
| Weekly  | 4    | `KEEP_WEEKLY`  |
| Monthly | 6    | `KEEP_MONTHLY` |

`forget` drops snapshots outside those windows; `--prune` then reclaims the now-unreferenced
data from the repository. Each run also does a cheap structural `restic check`; deep data
verification is the job of `restore-test.sh`.

## Restore runbook

The step-by-step recovery procedure lives in **[`docs/restore-runbook.md`](docs/restore-runbook.md)**.
It covers listing snapshots, a scoped single-path restore, a full bare-metal restore, and
running `restore-test.sh`. The runbook ends with a log table the operator fills in with the
date and result of each real test — it ships empty on purpose.

## Repository backend notes

restic is backend-agnostic; the repo is selected entirely by `RESTIC_REPOSITORY` in the
env file. Placeholders only — never commit a real repo URL or credentials:

- **Local / external disk:** `RESTIC_REPOSITORY=/srv/backups/restic-repo`
- **SFTP:** `RESTIC_REPOSITORY=sftp:backup-user@backup.example.internal:/srv/restic-repo`
  (key-based auth; the host stays out of git)
- **Backblaze B2:** `RESTIC_REPOSITORY=b2:example-bucket-name:host/path` with `B2_ACCOUNT_ID`
  and `B2_ACCOUNT_KEY` supplied via the env file, not the repo.

The repository is always encrypted; the encryption passphrase is read from a root-only file
pointed to by `RESTIC_PASSWORD_FILE` and is never stored in the repo.

## Decision and rationale

**Why systemd timers instead of cron?**

- **Missed runs are caught up.** `Persistent=true` records the last run; if the host was
  off at 02:00 the timer fires on next boot. Plain cron silently skips a run when the
  machine is asleep — exactly when a laptop or intermittently-powered homelab box misses it.
- **Every run is captured in the journal.** `journalctl -u restic-backup.service` gives
  timestamped stdout/stderr, exit status, and duration for each run. Cron's model is a mail
  to root that is usually unread and unsearchable.
- **Failure is a first-class state.** A non-zero exit marks the unit `failed`, visible in
  `systemctl --failed` and hookable via `OnFailure=`. Cron has no concept of a failed job.
- **Config and execution are separate, declarative units.** The `.timer` owns *when* and the
  `.service` owns *what*; schedule and dependencies (`After=network-online.target`) are
  declared, not encoded in a crontab line.
- **No overlap.** `Type=oneshot` plus the script's `flock` means a long backup can't be
  started again on top of itself.

The cost is that the schedule lives in two files instead of one crontab line — a worthwhile
trade for catch-up, logging, and failure semantics on a box that isn't always on.

## Layout

```
backup-restic/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── systemd/
│   ├── restic-backup.service
│   └── restic-backup.timer
├── scripts/
│   ├── backup.sh              # excludes, retention, prune, structural check
│   └── restore-test.sh        # restore latest + checksum vs live
└── docs/restore-runbook.md    # procedure to execute + dated test log (empty)
```

## Quick start

```bash
sudo install -d -m 700 /etc/restic-backup
sudo cp .env.example /etc/restic-backup/restic.env
sudo chmod 600 /etc/restic-backup/restic.env
# edit restic.env: set RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE, BACKUP_PATHS

# initialize the repo once (reads config from the env file):
sudo restic init      # with RESTIC_REPOSITORY / password exported from the env file

sudo cp scripts/*.sh /usr/local/sbin/
sudo cp systemd/restic-backup.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now restic-backup.timer
systemctl list-timers restic-backup.timer
```

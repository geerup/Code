# Restore runbook

Step-by-step recovery procedure for the restic repository. **This is a procedure to
execute, not a record of a completed test.** Run it, then fill in the log table at the
bottom with the real date and result. Nothing here claims a restore has already been done.

All commands read configuration from the same env file the backups use
(`/etc/restic-backup/restic.env`). Export it into the shell first:

```bash
set -a; source /etc/restic-backup/restic.env; set +a
export RESTIC_PASSWORD_FILE   # so restic can read the passphrase
```

Verify restic can reach the repository before anything else:

```bash
restic snapshots
```

If that lists snapshots, the repository, credentials, and passphrase are all good.

---

## 1. Inspect what is available

```bash
restic snapshots                 # list all snapshots (id, time, host, tags, paths)
restic snapshots --latest 1      # just the most recent
restic ls latest                 # file listing of the latest snapshot
restic stats latest              # size of the restorable set
```

Note the snapshot ID you intend to restore (or use `latest`).

## 2. Scoped restore of a single path (most common real recovery)

Recover one directory or file to a scratch location, then copy back what you need. Never
restore straight over a live path on the first attempt.

```bash
mkdir -p /var/tmp/restore
restic restore latest --target /var/tmp/restore --include /etc/ssh
# inspect, then copy back deliberately:
ls -la /var/tmp/restore/etc/ssh
# cp -a /var/tmp/restore/etc/ssh/sshd_config /etc/ssh/sshd_config
```

Restore a specific version by snapshot ID instead of `latest`:

```bash
restic restore <snapshot-id> --target /var/tmp/restore --include /path/needed
```

## 3. Full restore (bare-metal / disaster recovery)

On a fresh host: install restic, recreate `/etc/restic-backup/restic.env` and the
password file, then:

```bash
set -a; source /etc/restic-backup/restic.env; set +a
restic snapshots                          # confirm access
restic restore latest --target /mnt/recovery
# review, then rsync/copy into place from /mnt/recovery, or restore into / on a
# throwaway system you are rebuilding.
```

Order of operations that actually matters in a real disaster:

1. Rebuild the base OS and install restic.
2. Recover the **password file** and **repo credentials** first — without the passphrase
   the encrypted repo is unrecoverable. Keep these somewhere independent of the machine
   being backed up (password manager, sealed offline note).
3. `restic snapshots` to confirm access.
4. Restore config (`/etc`), then data, then re-enable services.

## 4. Automated verification (`restore-test.sh`)

`scripts/restore-test.sh` restores the latest snapshot into a scratch directory and
compares every restored file's SHA-256 against the live copy. Run it regularly (monthly)
and after any change to the backup configuration.

```bash
sudo /usr/local/sbin/restore-test.sh
# faster, scoped to one subtree:
sudo RESTORE_TEST_INCLUDE=/etc /usr/local/sbin/restore-test.sh
```

Reading the summary:

- **matched** — restored file is byte-identical to the live file. Good.
- **drifted** — the live file changed since the snapshot (normal for logs/databases;
  only worrying for files you expect to be static).
- **missing** — file was in the snapshot but no longer on the live system (deleted since).
- The test **fails** (non-zero exit) only if the restore itself fails or restores zero
  files. Checksum drift alone is not a failure.

## 5. Record the test

After a successful run, record it here. **This table starts empty on purpose — fill in a
row each time you actually run a restore test. Do not pre-populate it.**

| Date (YYYY-MM-DD) | Type (scoped / full / restore-test.sh) | Snapshot | Result (files matched / drifted / missing) | Notes |
|-------------------|----------------------------------------|----------|--------------------------------------------|-------|
|                   |                                        |          |                                            |       |

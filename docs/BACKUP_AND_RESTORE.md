# Backup And Restore

This document describes the narrow SQLite backup and restore procedure for `official-sources`.

Before running migrations on a persistent installation, create a database backup.

Never restore over an active SQLite database while ingestion, artifact download, MCP or API processes are running.

## Create A Backup

Use the SQLite online backup API through the CLI:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /opt/official-sources/data/backups/official_sources_YYYYMMDD_HHMMSS.sqlite
```

The command:

- copies the database with SQLite's online backup API;
- runs `PRAGMA quick_check` on the source database by default;
- runs `PRAGMA quick_check` on the backup database by default;
- compares row counts for known application tables;
- enforces a default minimum backup size of 1024 bytes;
- creates parent directories when needed;
- refuses to overwrite an existing file unless `--force` is passed;
- creates the backup with restrictive file permissions where the OS supports it;
- does not fetch network resources;
- does not call BOE APIs;
- does not call MCP tools;
- does not modify downstream projects.

Use `--force` only when replacing a known disposable backup file:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /tmp/official_sources_test.sqlite --force
```

Verification modes:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /path/to/backup.sqlite --quick-check

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /path/to/backup.sqlite --full-check

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /path/to/backup.sqlite --no-verify

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /path/to/backup.sqlite --min-size-bytes 1024
```

`quick_check` is the default for automated backups. It is faster and detects major SQLite corruption problems such as missing pages, malformed records, and invalid page links. It is suitable for daily operational backup verification.

`quick_check` limitation: it does not fully verify index consistency against table data. For example, it may not detect every case where a row exists in a table but the corresponding index entry is missing or inconsistent.

`full_check` is explicit through `--full-check`. It is slower, runs `PRAGMA integrity_check`, performs a fuller structural check including indexes, and is suitable for periodic manual audits or diagnostics.

Use `--full-check` when:

- index corruption is suspected;
- the server had an abnormal shutdown during a write-heavy ingestion run;
- a migration failed or was interrupted;
- SQLite reports unusual query or index behavior;
- a periodic manual audit is being performed;
- a backup is being prepared before a high-risk migration or deployment.

`--no-verify` skips automated verification only when explicitly passed. If verification fails after a backup file has been created, the file is kept with a `.failed` suffix for inspection and is not reported as successful.

Compression is not implemented. If operators compress backup files externally, validate the decompressed SQLite file before using it.

## Validate A Backup Copy

Validate a copied or restored database before using it:

```bash
official-sources --db-path /tmp/official_sources_restored.sqlite db status
official-sources --db-path /tmp/official_sources_restored.sqlite db migrate
official-sources --db-path /tmp/official_sources_restored.sqlite db validate
```

A small read-only smoke check should then query known stored data. Examples:

```bash
official-sources --db-path /tmp/official_sources_restored.sqlite status --date 2024-05-29
```

For programmatic checks, build a citation for a known BOE document or a consolidated-law block through the read-only Python or MCP paths.

## Manual Restore Procedure

1. Stop services and timers that may use the database.

```bash
sudo systemctl stop official-sources-boe-daily.timer
sudo systemctl stop official-sources-integrity-check.timer
sudo systemctl stop official-sources-boe-daily.service
sudo systemctl stop official-sources-integrity-check.service
```

2. Copy the current database aside before replacing it.

```bash
sudo cp /opt/official-sources/data/official_sources.sqlite \
  /opt/official-sources/data/backups/pre_restore_official_sources.sqlite
```

3. Restore the backup to the target database path.

```bash
sudo cp /opt/official-sources/data/backups/official_sources_YYYYMMDD_HHMMSS.sqlite \
  /opt/official-sources/data/official_sources.sqlite
```

4. Validate and migrate if needed.

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db migrate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

5. Run a small read-only smoke check.

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date 2024-05-29
```

6. Restart services and timers.

```bash
sudo systemctl start official-sources-boe-daily.timer
sudo systemctl start official-sources-integrity-check.timer
```

7. Check logs.

```bash
journalctl -u official-sources-boe-daily.service -n 100 --no-pager
journalctl -u official-sources-integrity-check.service -n 100 --no-pager
```

## VPS Deployment Prerequisite

Before deploying code that contains schema changes:

1. create a backup;
2. restore the backup to a temporary path;
3. run `db migrate`;
4. run `db validate`;
5. run a read-only smoke query;
6. only then migrate the active database during a maintenance window.

For the full deployment and rollback sequence, see `docs/PRE_DEPLOY_VPS_CHECKLIST.md`.

## Known Limitations

- Automatic restore is not implemented.
- Cloud backups are not implemented.
- Encryption is not implemented.
- Backup rotation is not implemented.
- Backup timers are documented as an operational idea, not installed by this repository.

# Pre-Deploy VPS Checklist

This checklist is for deploying or updating `official-sources` on a small private Ubuntu LTS VPS.

Do not deploy or migrate a persistent installation without a fresh backup and a restore rehearsal.
Do not expose MCP, SQLite, or admin operations to the public internet.

## 1. Local Validation Before Deployment

Run the repository validation commands locally before packaging or pulling changes on the VPS:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Equivalent commands without `rtk`:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

## 2. Expected VPS Layout

Recommended layout:

```text
/opt/official-sources/
|-- app/
|-- data/
|   |-- official_sources.sqlite
|   |-- artifacts/
|   `-- backups/
|-- logs/
`-- .env
```

`app/` contains the checked-out repository and virtual environment. `data/` contains
persistent state. `logs/` is optional if the systemd journal is the primary log store.

Prepare the directories:

```bash
sudo mkdir -p /opt/official-sources/app
sudo mkdir -p /opt/official-sources/data/artifacts
sudo mkdir -p /opt/official-sources/data/backups
sudo mkdir -p /opt/official-sources/logs
```

Use a dedicated non-root service user where feasible:

```bash
if ! id official-sources >/dev/null 2>&1; then
  sudo useradd --system --home /opt/official-sources --shell /usr/sbin/nologin official-sources
fi
sudo chown -R official-sources:official-sources /opt/official-sources
```

## 3. Application Installation

Install or update the application under `/opt/official-sources/app`:

```bash
cd /opt/official-sources/app
git clone <private-repository-url> .
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
official-sources --help
```

For an update, pull or copy the reviewed source tree into `app/`, activate the same virtual
environment, and reinstall with `python -m pip install -e .`.

## 4. Environment Variables

Create `/opt/official-sources/.env`:

```bash
OFFICIAL_SOURCES_DB_PATH=/opt/official-sources/data/official_sources.sqlite
OFFICIAL_SOURCES_ARTIFACT_DIR=/opt/official-sources/data/artifacts
OFFICIAL_SOURCES_BOE_REQUESTS_PER_SECOND=1
OFFICIAL_SOURCES_BOE_MAX_RETRIES=5
OFFICIAL_SOURCES_BOE_BACKOFF_BASE_SECONDS=1
OFFICIAL_SOURCES_BOE_BACKOFF_MAX_SECONDS=30
OFFICIAL_SOURCES_BOE_JITTER_SECONDS=0.25
```

The CLI reads `OFFICIAL_SOURCES_DB_PATH`, the legacy `OFFICIAL_SOURCES_DB`, and
`OFFICIAL_SOURCES_ARTIFACT_DIR`. MCP reads `OFFICIAL_SOURCES_DB_PATH` first and then the
legacy `OFFICIAL_SOURCES_DB`.

Do not commit `.env`. The current implementation does not require API keys.

Set restrictive permissions:

```bash
sudo chown root:official-sources /opt/official-sources/.env
sudo chmod 600 /opt/official-sources/.env
```

## 5. Backup Before Deploy Or Update

If a database already exists, create a backup before any code update, schema migration, or
systemd template change:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /opt/official-sources/data/backups/official_sources_YYYYMMDD_HHMMSS.sqlite
```

Rules:

- back up before migration;
- back up before code update;
- back up before systemd changes;
- default backup verification runs `PRAGMA quick_check` on source and backup;
- use `--full-check` before high-risk migrations, after abnormal shutdowns, or during periodic audits;
- row-count comparison and minimum backup size checks must pass;
- do not overwrite an existing backup unless using `--force` deliberately for a disposable file.

## 6. Database Initialization And Migration

Check migration state:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
```

For persistent VPS databases, `db status` should report `journal_mode=wal` and
`synchronous=normal`. WAL allows read-only consumers to keep reading while one writer is
active, but SQLite still has a single-writer model. If write concurrency grows beyond this
operational model, plan a PostgreSQL migration instead of treating WAL as a full database
server replacement.

Apply pending migrations:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db migrate
```

Validate the migrated schema:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Do not silently recreate an existing database. If the active database exists, back it up first.

## 7. Restore Rehearsal

Rehearse restore on a temporary copy, not the active database:

```bash
cp /opt/official-sources/data/backups/<backup>.sqlite /tmp/official_sources_restore_test.sqlite

official-sources --db-path /tmp/official_sources_restore_test.sqlite db status
official-sources --db-path /tmp/official_sources_restore_test.sqlite db migrate
official-sources --db-path /tmp/official_sources_restore_test.sqlite db validate
```

Remove the temporary copy after the rehearsal:

```bash
rm /tmp/official_sources_restore_test.sqlite
```

## 8. Smoke Checks

Run local read-only checks first:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  status --date today

official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

BOE publishes every day of the year except Sundays. National holidays, 24 December, and 31
December can still have BOE publication. If BOE returns `404 Not Found` or another observed
no-summary response for a Sunday, daily summary ingestion records
`ingestion_status=no_publication` and preserves `last_http_status`. This is a controlled
no-summary condition, not a system failure, and the systemd daily service should finish
successfully. Artifact download is skipped for that date.

Do not infer BOE no-publication from a generic holiday calendar. Non-Sunday `404`, network,
server, parser, storage, and schema errors must fail and be investigated unless a specific
non-Sunday date has been explicitly allowlisted from observed BOE API behavior. BORME
publication rules are different and must not be reused for BOE daily summary ingestion.

The following consolidated-law commands fetch from official BOE endpoints. Use them only when
a live BOE network smoke check is acceptable, and replace placeholders with a known official
identifier and block ID:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  boe-consolidated-get --identifier BOE-A-YYYY-NNNNN

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  boe-consolidated-index-get --identifier BOE-A-YYYY-NNNNN

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  boe-consolidated-block-get --identifier BOE-A-YYYY-NNNNN --block-id BLOCK_ID
```

Do not claim live BOE checks passed unless they were actually run.

Controlled project backfills must remain summary-first:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-boe-range --date-from YYYY-MM-DD --date-to YYYY-MM-DD \
  --skip-existing --continue-on-no-publication
```

Do not run a broad historical backfill without a fresh verified backup, estimated request
count, explicit date range, artifact policy, and written report. XML/HTML/PDF downloads remain
separate explicit steps, and PDF is never a default backfill artifact.

BDNS catalog and grants checks are optional live-network checks for grants workflows. Run them only
after backup, migration, and `db validate` have passed, and keep them bounded:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  preview-bdns-catalog --catalog sectores

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bdns-catalog --catalog sectores

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  export-bdns-grants --output /opt/official-sources/data/bdns-grants-preview.jsonl --limit 100
```

BDNS concesiones must remain scoped to one convocatoria. There is no approved global concessions
operation:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  preview-bdns-concesiones --num-conv CODIGO_BDNS --page-size 10

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bdns-concesiones --num-conv CODIGO_BDNS --page-size 10 --max-pages 1

official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  export-bdns-concessions --num-conv CODIGO_BDNS \
  --output /opt/official-sources/data/bdns-concessions-preview.jsonl
```

Default concesiones behavior redacts beneficiary name and person-id fields. Do not add
`--include-beneficiary-fields` unless the run has an explicit privacy/retention approval.

BDNS post-run checks:

- `db validate` still passes;
- BDNS command output reports `status=success`;
- source candidate counts did not change;
- artifact download attempt counts did not change;
- downstream repositories were not touched;
- concesiones runs used `--num-conv` and did not use `--include-beneficiary-fields` without
  approval;
- exported JSONL path and record count are recorded in the deployment report.

## 9. Systemd Installation

Templates live in `deploy/systemd/` and assume:

- service user: `official-sources`;
- working directory: `/opt/official-sources/app`;
- executable: `/opt/official-sources/app/.venv/bin/official-sources`;
- environment file: `/opt/official-sources/.env`.

Install the templates:

```bash
sudo cp deploy/systemd/official-sources-boe-daily.service /etc/systemd/system/
sudo cp deploy/systemd/official-sources-boe-daily.timer /etc/systemd/system/
sudo cp deploy/systemd/official-sources-integrity-check.service /etc/systemd/system/
sudo cp deploy/systemd/official-sources-integrity-check.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

Before enabling timers, verify the installed service files:

```bash
systemctl cat official-sources-boe-daily.service
systemctl cat official-sources-integrity-check.service
```

Enable timers only if paths, user, group, and environment file are correct:

```bash
sudo systemctl enable official-sources-boe-daily.timer
sudo systemctl enable official-sources-integrity-check.timer
sudo systemctl start official-sources-boe-daily.timer
sudo systemctl start official-sources-integrity-check.timer
sudo systemctl status official-sources-boe-daily.timer
sudo systemctl status official-sources-integrity-check.timer
```

Check logs:

```bash
journalctl -u official-sources-boe-daily.service -n 100 --no-pager
journalctl -u official-sources-integrity-check.service -n 100 --no-pager
```

Do not enable broken timers.

## 10. MCP Privacy Check

- This MCP server has no authentication.
- MCP must not be publicly exposed.
- No public port should be opened for MCP.
- Use local stdio, localhost, SSH tunnel, or private VPN access only.
- Exposing it on a public interface without authentication is a security gap.
- Do not expose MCP through Cloudflare Tunnel, public Nginx, public Docker port mapping, or `0.0.0.0` unless a proper authentication and authorization layer is added.
- MCP tools must not write to downstream projects.
- MCP tools must not perform arbitrary downloads.
- MCP tools must not execute shell commands.
- BDNS catalog refresh, grant export, and scoped concesiones ingestion/export are CLI operations,
  not public MCP live-fetch/write tools. MCP exposes only read-only cache views.
- BDNS concesiones must not be ingested globally; beneficiary fields are redacted by default.

Start MCP only in a private operator session or private process manager:

```bash
OFFICIAL_SOURCES_DB_PATH=/opt/official-sources/data/official_sources.sqlite \
  /opt/official-sources/app/.venv/bin/python -m official_sources.mcp.server
```

Stop it with the owning terminal or process manager. Do not add a public listener in this task.

## 11. Manual Rollback

Never restore over an active SQLite database while ingestion, artifact download, MCP or API
processes are running.

1. Stop timers and services:

```bash
sudo systemctl stop official-sources-boe-daily.timer
sudo systemctl stop official-sources-integrity-check.timer
sudo systemctl stop official-sources-boe-daily.service
sudo systemctl stop official-sources-integrity-check.service
```

2. Back up the current broken database aside:

```bash
sudo cp /opt/official-sources/data/official_sources.sqlite \
  /opt/official-sources/data/backups/broken_official_sources_YYYYMMDD_HHMMSS.sqlite
```

3. Restore the previous backup:

```bash
sudo cp /opt/official-sources/data/backups/<previous-good-backup>.sqlite \
  /opt/official-sources/data/official_sources.sqlite
```

4. Validate and smoke check:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date today
```

5. Restart timers:

```bash
sudo systemctl start official-sources-boe-daily.timer
sudo systemctl start official-sources-integrity-check.timer
```

6. Inspect logs:

```bash
journalctl -u official-sources-boe-daily.service -n 100 --no-pager
journalctl -u official-sources-integrity-check.service -n 100 --no-pager
```

## 12. Security Checklist

- MCP is not publicly exposed.
- SQLite is not publicly exposed.
- SSH access is preferably through Tailscale or another private network.
- No arbitrary download endpoint exists.
- No secrets are committed.
- Backup file permissions are checked.
- systemd services run as the non-root `official-sources` user.
- Artifact directory permissions are checked.
- Logs do not contain raw legal text unnecessarily.
- Cloudflare Tunnel is not needed unless exposing a controlled HTTP API.
- `official-sources` does not write into downstream projects.

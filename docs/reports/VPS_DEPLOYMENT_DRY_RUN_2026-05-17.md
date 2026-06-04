# VPS Deployment Dry Run - 2026-05-17

## Scope

TASK-004A was executed as a local dry-run only. No real SSH or private VPS access was
available in this environment, so no VPS deployment, systemd installation, timer enablement,
firewall check, Tailscale check, or private network inspection was performed.

This report does not claim a real deployment.

## Environment

- Operator environment: Windows workspace at `G:\_Proyectos\mcpspain\official-sources`.
- Repository metadata: no `.git` directory is present in this source tree.
- Python execution: `rtk python`.
- Local rehearsal data path: `<tmp>/official-sources-task004a-20260517`.
- Target VPS assumption documented for manual execution: Ubuntu 24.04 LTS, Python 3.12+,
  private access, non-root `official-sources` user, no public MCP exposure.

## Preflight Commands Run Locally

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Results:

- Tests: `144 passed`.
- Ruff lint: `All checks passed!`.
- Ruff format check: `55 files already formatted`.

## CLI Availability Rehearsal

The `official-sources` console script was not installed globally in this Windows shell, so the
CLI was validated through the source entry point:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --help
```

Result: CLI help printed successfully.

The equivalent VPS command after editable installation is:

```bash
official-sources --help
```

## Local Database Migration Rehearsal

Commands:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources.sqlite db validate
```

Results:

- Initial status: `current_version=0 latest_version=5 pending_migrations=5 status=pending`.
- Migration: `current_version=5 latest_version=5 applied_migrations=1,2,3,4,5 status=migrated`.
- Validation: `current_version=5 latest_version=5 status=valid`.

## Verified Backup And Restore-Copy Rehearsal

Backup command:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources.sqlite db backup --output <tmp>/official-sources-task004a-20260517/backups/official_sources_20260517_000000.sqlite
```

Backup result:

```text
pages=26 verification=quick_check source_check=ok backup_check=ok size_bytes=110592 status=success
```

Restore-copy commands:

```bash
Copy-Item -Force G:\tmp\official-sources-task004a-20260517\backups\official_sources_20260517_000000.sqlite G:\tmp\official-sources-task004a-20260517\official_sources_restore_test.sqlite
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources_restore_test.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources_restore_test.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources_restore_test.sqlite db validate
```

Restore-copy results:

- Status: `current_version=5 latest_version=5 pending_migrations=0 status=up_to_date`.
- Migration: `current_version=5 latest_version=5 applied_migrations=none status=up_to_date`.
- Validation: `current_version=5 latest_version=5 status=valid`.

The active database was not overwritten during the rehearsal.

## Smoke Check

Command:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path <tmp>/official-sources-task004a-20260517/official_sources_restore_test.sqlite --artifact-dir <tmp>/official-sources-task004a-20260517/artifacts status --date today
```

Result:

```text
command_started=status source_code=BOE target_date=2026-05-17
ingestion_status=none documents=0 xml_files=0 html_files=0 pdf_files=0 download_attempts=0 download_success=0 download_skipped=0 download_changed=0 download_failed=0 integrity_warnings=0 failed_downloads=0
```

No live BOE calls were run during this dry-run.

## Exact Manual VPS Commands

Prepare directories and service user:

```bash
sudo mkdir -p /opt/official-sources/app
sudo mkdir -p /opt/official-sources/data/artifacts
sudo mkdir -p /opt/official-sources/data/backups
sudo mkdir -p /opt/official-sources/logs
sudo useradd --system --home /opt/official-sources --shell /usr/sbin/nologin official-sources || true
sudo chown -R official-sources:official-sources /opt/official-sources
```

Install application:

```bash
cd /opt/official-sources/app
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
official-sources --help
```

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

Then set permissions:

```bash
sudo chmod 600 /opt/official-sources/.env
```

Initialize and migrate:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db migrate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Create verified backup and rehearse restore:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup --output /opt/official-sources/data/backups/official_sources_YYYYMMDD_HHMMSS.sqlite

cp /opt/official-sources/data/backups/<backup>.sqlite /tmp/official_sources_restore_test.sqlite
official-sources --db-path /tmp/official_sources_restore_test.sqlite db status
official-sources --db-path /tmp/official_sources_restore_test.sqlite db migrate
official-sources --db-path /tmp/official_sources_restore_test.sqlite db validate
```

Run smoke checks:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  status --date today
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Install systemd templates:

```bash
sudo cp deploy/systemd/official-sources-boe-daily.service /etc/systemd/system/
sudo cp deploy/systemd/official-sources-boe-daily.timer /etc/systemd/system/
sudo cp deploy/systemd/official-sources-integrity-check.service /etc/systemd/system/
sudo cp deploy/systemd/official-sources-integrity-check.timer /etc/systemd/system/
sudo systemctl daemon-reload
systemctl cat official-sources-boe-daily.service
systemctl cat official-sources-integrity-check.service
```

Enable timers only after confirming paths, user, group, virtual environment, and `.env`:

```bash
sudo systemctl enable official-sources-boe-daily.timer
sudo systemctl enable official-sources-integrity-check.timer
sudo systemctl start official-sources-boe-daily.timer
sudo systemctl start official-sources-integrity-check.timer
sudo systemctl status official-sources-boe-daily.timer
sudo systemctl status official-sources-integrity-check.timer
journalctl -u official-sources-boe-daily.service -n 100 --no-pager
journalctl -u official-sources-integrity-check.service -n 100 --no-pager
```

## Systemd Status

Systemd was not installed or enabled in this local Windows dry-run.

## MCP Privacy Status

MCP was not started on a VPS. The documented requirement is:

- no public MCP listener;
- no public SQLite access;
- access only through stdio, localhost, SSH tunnel, or private VPN/Tailscale;
- no Cloudflare Tunnel for MCP;
- no public Nginx proxy for MCP;
- no public Docker port mapping for MCP;
- no MCP write tools;
- no MCP arbitrary download tool;
- no MCP shell execution tool.

## Rollback Procedure For Manual VPS Use

Never restore over an active SQLite database while ingestion, artifact download, MCP or API
processes are running.

1. Stop timers and services.
2. Back up the current broken database aside.
3. Restore a previous known-good backup.
4. Run `db validate`.
5. Run read-only smoke checks.
6. Restart timers and services.
7. Inspect `journalctl` logs.

## Failures Or Gaps

- No real VPS deployment was performed.
- No SSH, firewall, Tailscale, private VPN, or network exposure checks were performed.
- No `systemctl` or `journalctl` commands were executed.
- No live BOE smoke calls were run.
- The local `official-sources` console script was not installed in the Windows shell; CLI behavior
  was rehearsed through the source entry point.

## Manual Steps Remaining

1. Create or access the private Ubuntu 24.04 VPS.
2. Prepare `/opt/official-sources` directories and the dedicated service user.
3. Copy or clone the reviewed repository into `/opt/official-sources/app`.
4. Create the Python 3.12 virtual environment and install the package.
5. Create `/opt/official-sources/.env` with restrictive permissions.
6. Run `db status`, backup first if a DB exists, `db migrate`, and `db validate`.
7. Create a verified backup and rehearse restore on `/tmp/official_sources_restore_test.sqlite`.
8. Run `status --date today` and any explicitly approved live BOE smoke checks.
9. Install systemd templates, inspect them, then enable timers only if correct.
10. Confirm MCP remains private and read-only.
11. Document the real VPS results in `docs/reports/VPS_DEPLOYMENT_REHEARSAL_YYYY-MM-DD.md`.

## Conclusion

The local dry-run passed for validation, CLI entry point, migration to schema version 5,
verified backup, restore-copy validation, and a no-network status smoke check. Real VPS
installation and service enablement remain manual and unverified.

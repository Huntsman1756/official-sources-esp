# BOE 30-day summary backfill rehearsal - 2026-05-17

## Summary

TASK-004C-RUN1B deployed the BOE calendar/WAL patch to the private VPS and reran the controlled
30-day BOE summary-only backfill command.

The run covered the inclusive range `2026-04-18` through `2026-05-17` with conservative request
policy, `--skip-existing`, `--continue-on-no-publication`, `--stop-on-error`, and `--max-days 30`.

No XML, HTML, or PDF artifact downloads were run. No keyword candidate prefiltering was run. No
downstream integration was run.

The backfill command completed successfully and skipped all 30 dates because the range had already
been ingested during TASK-004C-RUN1.

## Environment

- Host: private VPS, public IP redacted.
- Date/time UTC: `2026-05-17T18:21:09Z`.
- Application path: `/opt/official-sources/app`.
- Database path: `/opt/official-sources/data/official_sources.sqlite`.
- Artifact path: `/opt/official-sources/data/artifacts`.
- Commit before deploy: `607b96c`.
- Deployed commit after pull: `15d5077`.
- Schema version: `current_version=6 latest_version=6`.

## Pre-Deploy State

Before deploying the patch:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 pending_migrations=0 status=up_to_date
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 status=valid
```

The old deployed CLI did not yet report `journal_mode` or `synchronous`.

## Pre-Deploy Backup

Verified backup before the successful deployment:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_15d5077_deploy_20260517_182109.sqlite
pages=2317
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=9490432
status=success
```

An earlier attempt also created a successful pre-deploy backup at
`official_sources_before_15d5077_deploy_20260517_182008.sqlite`, but that attempt stopped before
deployment because `git` rejected root access to the repository as `dubious ownership`. The
successful deployment used the `official-sources` service user for Git and package reinstall.

## Deployment

Commands executed:

```bash
cd /opt/official-sources/app
sudo -u official-sources git fetch origin
sudo -u official-sources git checkout main
sudo -u official-sources git pull --ff-only origin main
sudo -u official-sources git rev-parse --short HEAD
sudo -u official-sources /opt/official-sources/app/.venv/bin/python -m pip install -e .
sudo -u official-sources /opt/official-sources/app/.venv/bin/official-sources --help
```

Result:

- Deployed commit: `15d5077`.
- Editable package reinstall: success.
- CLI help smoke check: success.

Pip emitted a warning about a leftover temporary distribution directory in the virtual
environment:

```text
WARNING: Failed to remove contents in a temporary directory ... ~fficial_sources-0.1.0.dist-info
WARNING: Ignoring invalid distribution ~fficial-sources ...
```

This did not block installation or CLI execution. It should be cleaned during a later maintenance
window if the warning persists.

## Migration And WAL Status

Commands executed:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db migrate

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db status
```

Result:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 applied_migrations=none status=up_to_date
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 status=valid
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 pending_migrations=0 journal_mode=wal synchronous=normal status=up_to_date
```

WAL check: passed.

## Range Command

Command executed:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-boe-range \
  --date-from 2026-04-18 \
  --date-to 2026-05-17 \
  --skip-existing \
  --continue-on-no-publication \
  --stop-on-error \
  --max-days 30 \
  --sleep-seconds 1
```

CLI result:

```text
processed=0 skipped=30 success=0 no_publication=0 failed=0 days=30
```

The command exited successfully. Because `--skip-existing` was enabled and all dates were already
present from TASK-004C-RUN1, no live BOE summary requests were made during RUN1B.

## Final Range State

Final latest summary state for the full 30-day range:

- Latest summary rows: `30`.
- Successful publication days: `25`.
- No-publication days: `5`.
- Failed days: `0`.
- HTTP status summary: `200:25,404:5`.
- Documents fetched: `3896`.
- Documents new: `3896`.
- Documents updated: `0`.
- Retry count total: `0`.
- Throttle events: `6`.

No non-Sunday `404` was observed during this run. Existing no-publication dates in the range are
the Sunday no-summary outcomes from the previous controlled run.

## Selected Status Outputs

Start date:

```text
target_date=2026-04-18
summary_ingestion_status=success
summary_last_http_status=200
summary_retry_count=0
summary_throttle_triggered=0
documents=314
xml_files=0
html_files=0
pdf_files=0
artifact_download_attempts=0
artifact_http_status_summary=none
```

End date:

```text
target_date=2026-05-17
summary_ingestion_status=no_publication
summary_last_http_status=404
summary_retry_count=0
summary_throttle_triggered=0
documents=0
xml_files=0
html_files=0
pdf_files=0
artifact_download_attempts=0
artifact_http_status_summary=none
```

Weekday publication date:

```text
target_date=2026-04-20
summary_ingestion_status=success
summary_last_http_status=200
summary_retry_count=0
summary_throttle_triggered=1
documents=122
xml_files=0
html_files=0
pdf_files=0
artifact_download_attempts=0
artifact_http_status_summary=none
```

## Database Validation

Post-run validation passed:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 status=valid
```

## Artifact Directory

- Before RUN1B range command: `22M`.
- After RUN1B range command: `22M`.

The artifact directory did not grow. `find` showed existing files from the earlier
`2024-05-29` known-date artifact validation only. This task did not create XML, HTML, or PDF
artifacts.

## MCP Privacy Check

The socket check showed:

- no MCP, FastMCP, Python, Uvicorn, or `official-sources` public listener;
- no SQLite exposure;
- SSH listening publicly, as expected for VPS access;
- loopback DNS listeners from `systemd-resolved`, as expected.

The public IP observed in socket output is intentionally not recorded in this report.

## Post-Run Backup

Verified backup after the successful command:

```text
backup_path=/opt/official-sources/data/backups/official_sources_after_30d_backfill_20260517_182117.sqlite
pages=2317
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=9490432
status=success
```

## Known Limitations

- RUN1B did not make live BOE requests because all 30 dates were already present and
  `--skip-existing` worked as intended.
- This remains a 30-day summary-only rehearsal, not a 24-month backfill.
- No artifacts were downloaded for the range.
- No keyword candidate prefiltering was run.
- No downstream project integration was run.
- No full historical BOE archive download was attempted.
- The VPS virtual environment has a non-blocking pip warning about a leftover temporary
  distribution directory.

## Next Recommended Task

Run a candidate prefilter rehearsal over this 30-day locally stored summary range, with no live BOE
requests and no artifact downloads, then review false positives before authorizing a larger
summary-only range.

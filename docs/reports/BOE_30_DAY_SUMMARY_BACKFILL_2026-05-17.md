# BOE 30-day summary backfill rehearsal - 2026-05-17

## Summary

TASK-004C-RUN1 executed a controlled BOE summary-only backfill on the private VPS.

The run covered the inclusive range `2026-04-18` through `2026-05-17` with conservative request
policy, `--skip-existing`, `--continue-on-no-publication`, `--stop-on-error`, and `--max-days 30`.

No XML, HTML, or PDF artifact downloads were run. No keyword candidate prefiltering was run.

## Environment

- Host: private VPS, public IP redacted.
- Date/time UTC: `2026-05-17T18:08:56Z`.
- Application path: `/opt/official-sources/app`.
- Database path: `/opt/official-sources/data/official_sources.sqlite`.
- Artifact path: `/opt/official-sources/data/artifacts`.
- Deployed commit after pull: `607b96c`.
- Schema status before run: `current_version=6 latest_version=6 status=valid`.

## Commands Executed

The application was updated on the VPS before the operational run:

```bash
cd /opt/official-sources/app
git fetch origin main
git checkout main
git pull --ff-only origin main
git rev-parse --short HEAD
.venv/bin/python -m pip install -e .
```

Pre-run database checks:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db status

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Pre-run verified backup:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_before_30d_backfill_20260517_180859.sqlite
```

Controlled summary-only range ingestion:

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

Selected status checks:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  status --date 2026-04-18

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  status --date 2026-05-17
```

Post-run validation and privacy checks:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate

du -sh /opt/official-sources/data/artifacts
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
ss -tulpn
```

Post-run verified backup:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_after_30d_backfill_20260517_180948.sqlite
```

## Pre-Run Backup

- Backup path: `/opt/official-sources/data/backups/official_sources_before_30d_backfill_20260517_180859.sqlite`.
- Verification mode: `quick_check`.
- Source check: `ok`.
- Backup check: `ok`.
- Pages: `460`.
- Size: `1884160` bytes.
- Status: `success`.

## Range Ingestion Result

CLI output:

```text
processed=29 skipped=1 success=25 no_publication=4 failed=0 days=30
```

The range contained one already-recorded date, so the command processed 29 dates and skipped 1
existing date. The final database state for the full 30-day range was:

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

No artifact downloads were triggered by range ingestion.

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

The first successful publication date in the run was `2026-04-18`, so it is covered by the start
date status check.

## Database Validation

Post-run validation passed:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=6 latest_version=6 status=valid
```

## Artifact Directory

- Before run: `22M`.
- After run: `22M`.

The artifact directory size did not grow. Existing artifacts were from earlier controlled
known-date validation; this task did not create XML, HTML, or PDF files.

## MCP Privacy Check

The socket check showed:

- no MCP, FastMCP, Python, Uvicorn, or `official-sources` public listener;
- no SQLite exposure;
- SSH listening publicly, as expected for VPS access;
- loopback DNS listeners from `systemd-resolved`, as expected.

The public IP observed in socket output is intentionally not recorded in this report.

## Post-Run Backup

- Backup path: `/opt/official-sources/data/backups/official_sources_after_30d_backfill_20260517_180948.sqlite`.
- Verification mode: `quick_check`.
- Source check: `ok`.
- Backup check: `ok`.
- Pages: `2317`.
- Size: `9490432` bytes.
- Status: `success`.

## Known Limitations

- This was a 30-day summary-only rehearsal, not a 24-month backfill.
- No artifacts were downloaded for the newly ingested dates.
- No keyword candidate prefiltering was run.
- No downstream project integration was run.
- No full historical BOE archive download was attempted.

## Next Recommended Task

Run a candidate prefilter rehearsal over this 30-day locally stored summary range, with no live BOE
requests and no artifact downloads, then review false positives before authorizing a larger
summary-only range.

# VPS first BOE service run fix - 2026-05-17

## Original Failure Summary

The first forced BOE daily service run failed on the VPS because BOE returned `404 Not Found`
for:

```text
/datosabiertos/api/boe/sumario/20260517
```

The previous behavior treated that response as a hard ingestion failure. The service exited
non-zero, no artifacts were created, and the run stored the HTTP 404 only in `error_message`;
`last_http_status` remained `null`.

## Code And Configuration Changes

- Added controlled ingestion status: `no_publication`.
- Added migration `0006_ingestion_no_publication_status` so `ingestion_runs.status` accepts
  `no_publication`.
- Added `BOESummaryNotFoundError` for BOE daily summary `404`.
- Preserved `last_http_status=404`, `retry_count=0`, and `throttle_triggered=false` for BOE
  summary no-publication days.
- Made `ingest-boe-summary` exit with status code `0` for `no_publication`.
- Kept real technical failures as `failed` with non-zero CLI exit.
- Updated `status --date` output to include `last_http_status`.
- Made `download-boe-artifacts` skip without creating another ingestion run when the latest run
  for the date is `no_publication`.
- Documented BOE summary `404` as a controlled no-summary condition.

No systemd template change was required.

## Local Validation

Commands:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Results:

```text
152 passed
All checks passed!
56 files already formatted
```

## VPS Deployment

Deployment target: private VPS, public IP redacted.

Commands performed:

```bash
sudo -u official-sources /opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_before_no_publication_fix_20260517_173237.sqlite

cd /opt/official-sources/app
sudo -u official-sources git fetch origin main
sudo -u official-sources git checkout main
sudo -u official-sources git pull --ff-only origin main
sudo -u official-sources git rev-parse --short HEAD
sudo -u official-sources .venv/bin/python -m pip install -e .
```

Results:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_no_publication_fix_20260517_173237.sqlite
verification=quick_check source_check=ok backup_check=ok size_bytes=106496 status=success
deployed_commit=a942899
package reinstall succeeded
```

## VPS Migration And Validation

Commands:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db status

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db migrate

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Results:

```text
current_version=5 latest_version=6 pending_migrations=1 status=pending
current_version=6 latest_version=6 applied_migrations=6 status=migrated
current_version=6 latest_version=6 status=valid
```

## Forced Systemd Run After Fix

Command:

```bash
sudo systemctl start official-sources-boe-daily.service
```

Result:

```text
service_start_exit=0
official-sources-boe-daily.service: Deactivated successfully.
ExecStart ingest-boe-summary: status=0/SUCCESS
ExecStart download-boe-artifacts: status=0/SUCCESS
ExecStart status: status=0/SUCCESS
```

## Journal Summary

Relevant journal lines after the fix:

```text
command_started=ingest-boe-summary source_code=BOE target_date=2026-05-17
status=no_publication documents_fetched=0 documents_new=0 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=404
command_started=download-boe-artifacts source_code=BOE target_date=2026-05-17
downloaded=0 skipped=0 changed=0 failed=0 retries=0 status=no_publication last_http_status=404
command_started=status source_code=BOE target_date=2026-05-17
ingestion_status=no_publication last_http_status=404 documents=0 xml_files=0 html_files=0 pdf_files=0 download_attempts=0 download_success=0 download_skipped=0 download_changed=0 download_failed=0 integrity_warnings=0 failed_downloads=0
official-sources-boe-daily.service: Deactivated successfully.
```

No retry, throttle, 429, 503, or 5xx event was observed.

## Status After Fix

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  status --date today
```

Result:

```text
command_started=status source_code=BOE target_date=2026-05-17
ingestion_status=no_publication last_http_status=404 documents=0 xml_files=0 html_files=0 pdf_files=0 download_attempts=0 download_success=0 download_skipped=0 download_changed=0 download_failed=0 integrity_warnings=0 failed_downloads=0
```

## Artifact And Backup State

Artifact directory:

```text
/opt/official-sources/data/artifacts: 4.0K
```

No artifacts were created because the day remained `no_publication`.

Backups:

```text
official_sources_20260517_170440.sqlite
official_sources_before_no_publication_fix_20260517_173237.sqlite
```

No post-run backup was created because no documents or artifacts changed beyond the controlled
ingestion audit row.

## MCP Privacy Check

Observed listeners after the fix:

```text
SSH public listener
systemd-resolved loopback DNS listeners
```

No `official-sources`, MCP, Python, Uvicorn, or FastMCP public listener was running. SQLite was
not exposed over the network.

## Whether Real BOE Ingestion Occurred

No document ingestion occurred. BOE still returned no summary for `2026-05-17`, and the corrected
behavior recorded this as `no_publication` with `last_http_status=404`.

## Known Limitations

- This run validates the no-publication path, not a successful BOE publication-day ingestion with
  document and artifact downloads.
- The next successful publication-day run should still be observed through systemd to validate
  end-to-end document ingestion and artifact caching on the VPS.

## Next Recommended Task

TASK-004A-FOLLOWUP2: observe the next scheduled BOE daily timer on a publication day, or run one
controlled manual service execution for a known publication date if end-to-end artifact download
must be proven before waiting for the timer.

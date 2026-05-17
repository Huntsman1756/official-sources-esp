# VPS first BOE service run follow-up - 2026-05-17

## Summary

TASK-004A-FOLLOWUP was executed against the private VPS deployment.

The BOE daily service was started once through systemd. The service did not complete
successfully because the first `ExecStart` command, `official-sources ingest-boe-summary
--date today`, received `404 Not Found` from the BOE daily summary API for target date
`2026-05-17`.

No retry was performed after inspecting logs and database state.

## Environment

- Host: `ubuntu-4gb-nbg1-8`
- Date/time UTC: `2026-05-17T17:15:46Z` through `2026-05-17T17:16:20Z`
- SSH target: redacted public IP
- App path: `/opt/official-sources/app`
- Database path: `/opt/official-sources/data/official_sources.sqlite`
- Artifact path: `/opt/official-sources/data/artifacts`
- Backup path: `/opt/official-sources/data/backups`
- Service user: `official-sources`
- Deployed commit: `c5b6350`

## Service Definition Inspected

Command:

```bash
sudo systemctl cat official-sources-boe-daily.service
```

Observed configuration:

```text
Type=oneshot
User=official-sources
Group=official-sources
WorkingDirectory=/opt/official-sources/app
EnvironmentFile=/opt/official-sources/.env
ExecStart=/opt/official-sources/app/.venv/bin/official-sources ingest-boe-summary --date today
ExecStart=/opt/official-sources/app/.venv/bin/official-sources download-boe-artifacts --date today --types xml,html,pdf
ExecStart=/opt/official-sources/app/.venv/bin/official-sources status --date today
NoNewPrivileges=true
PrivateTmp=true
```

Environment file values inspected:

```text
OFFICIAL_SOURCES_DB_PATH=/opt/official-sources/data/official_sources.sqlite
OFFICIAL_SOURCES_ARTIFACT_DIR=/opt/official-sources/data/artifacts
OFFICIAL_SOURCES_BOE_REQUESTS_PER_SECOND=1
OFFICIAL_SOURCES_BOE_MAX_RETRIES=5
OFFICIAL_SOURCES_BOE_BACKOFF_BASE_SECONDS=1
OFFICIAL_SOURCES_BOE_BACKOFF_MAX_SECONDS=30
OFFICIAL_SOURCES_BOE_JITTER_SECONDS=0.25
```

The user, working directory, database path, artifact path, and executable path were correct.

## Timer State Before Manual Run

Commands:

```bash
sudo systemctl status official-sources-boe-daily.timer --no-pager
sudo systemctl status official-sources-boe-daily.service --no-pager
systemctl list-timers --all official-sources-* --no-pager
```

Observed state:

```text
official-sources-boe-daily.timer: active (waiting)
official-sources-boe-daily.service: inactive (dead)
next BOE daily timer run: 2026-05-18 07:30:00 UTC
next integrity timer run: 2026-05-18 12:00:00 UTC
```

## Manual Service Execution

Command executed once:

```bash
sudo systemctl start official-sources-boe-daily.service
```

Result:

```text
Job for official-sources-boe-daily.service failed because the control process exited with error code.
```

Service status:

```text
Active: failed (Result: exit-code)
Process: ExecStart=/opt/official-sources/app/.venv/bin/official-sources ingest-boe-summary --date today
code=exited, status=1/FAILURE
```

The service is a `oneshot` unit. It failed during the first command, so artifact download and
final status `ExecStart` commands were not executed by systemd.

## Journal Summary

Command:

```bash
sudo journalctl -u official-sources-boe-daily.service -n 300 --no-pager
```

Relevant log lines:

```text
command_started=ingest-boe-summary source_code=BOE target_date=2026-05-17
status=failed documents_fetched=0 documents_new=0 documents_updated=0
official-sources-boe-daily.service: Main process exited, code=exited, status=1/FAILURE
official-sources-boe-daily.service: Failed with result 'exit-code'.
```

The journal did not show 429, 503, 5xx, `Retry-After`, or artifact download activity.

## Database Failure Detail

Latest `ingestion_runs` row was inspected without making another BOE request.

Observed row:

```json
{
  "id": 1,
  "target_date": "2026-05-17",
  "status": "failed",
  "documents_fetched": 0,
  "documents_new": 0,
  "documents_updated": 0,
  "error_message": "Client error '404 Not Found' for url 'https://www.boe.es/datosabiertos/api/boe/sumario/20260517'",
  "retry_count": 0,
  "throttle_triggered": 0,
  "last_http_status": null,
  "started_at": "2026-05-17T17:16:20.080190+00:00",
  "finished_at": "2026-05-17T17:16:20.264350+00:00"
}
```

Interpretation: a live BOE request was attempted, but no BOE daily summary was available at the
target URL for `2026-05-17`. The target date was Sunday, 2026-05-17, so this may be a normal
no-publication day rather than an infrastructure failure. This was not retried against another
BOE date during this follow-up.

## Retry and Throttle Summary

- Retry performed by operator: no.
- Application retry count recorded: `0`.
- Throttle/backoff recorded: `false`.
- 429 observed: no.
- 503 or 5xx observed: no.
- `Retry-After` observed: no.
- Final BOE error: `404 Not Found`.
- Audit note: the `error_message` captured the HTTP 404, but `last_http_status` was recorded as
  `null` for this failed run.

## Database Validation

Commands:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db status

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Results:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=5 latest_version=5 pending_migrations=0 status=up_to_date
database_path=/opt/official-sources/data/official_sources.sqlite current_version=5 latest_version=5 status=valid
```

## Today Status

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  status --date today
```

Result:

```text
command_started=status source_code=BOE target_date=2026-05-17
ingestion_status=failed documents=0 xml_files=0 html_files=0 pdf_files=0 download_attempts=0 download_success=0 download_skipped=0 download_changed=0 download_failed=0 integrity_warnings=0 failed_downloads=0
```

## Artifact Directory

Commands:

```bash
du -sh /opt/official-sources/data/artifacts
find /opt/official-sources/data/artifacts -type f | head -50
```

Results:

```text
4.0K /opt/official-sources/data/artifacts
```

No artifact files were created because the service failed before artifact download.

## Database Size and Backups

Commands:

```bash
ls -lh /opt/official-sources/data/official_sources.sqlite
ls -lh /opt/official-sources/data/backups | tail -20
```

Results:

```text
/opt/official-sources/data/official_sources.sqlite: 104K
official_sources_20260517_170440.sqlite: 104K
```

No post-run backup was created because the service run failed. The previous deployment rehearsal
backup remains present.

## MCP Privacy Check

Commands:

```bash
ss -tulpn
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp'
```

Result:

```text
No official-sources, MCP, Python, Uvicorn, or FastMCP listener was found.
Public listeners observed: SSH only.
Loopback DNS listeners from systemd-resolved were present and expected.
SQLite was not exposed over the network.
```

MCP remained private and stopped.

## Failures

- `official-sources-boe-daily.service` failed with `status=1/FAILURE`.
- The failure occurred during `ingest-boe-summary --date today`.
- BOE returned `404 Not Found` for the target daily summary URL.
- No documents were ingested.
- No XML, HTML, or PDF artifacts were downloaded.
- No post-run backup was created.

## Manual Steps Remaining

- Allow the next scheduled BOE daily timer to run on `2026-05-18 07:30:00 UTC`, then inspect the
  same status and journal outputs.
- Alternatively, perform one controlled manual run on a known BOE publication date if the goal is
  to prove end-to-end ingestion before waiting for the next timer.
- Consider hardening the daily ingestion behavior for no-publication days so an expected BOE 404
  can be represented as an explicit operational state instead of a generic service failure.
- Consider ensuring failed HTTP responses persist `last_http_status=404` in `ingestion_runs`.

## Next Recommended Task

TASK-004A-FIX1: define and validate the operational behavior for BOE no-publication days and failed
HTTP status auditing before starting downstream pilot integration.

## Follow-up Correction

TASK-004A-FIX1 defines the controlled status `no_publication` for BOE daily summary `404`
responses. BOE documents summary API `404` as requested information not existing. For daily
summary ingestion, this is now treated as a no-summary/no-publication condition rather than
as a hard systemd failure. The corrected behavior persists `last_http_status=404`, keeps all
document counts at zero, skips artifact download for that date, and lets the CLI exit with
status code `0`. Real network, server, parser, storage, and schema failures remain
`failed` and exit non-zero.

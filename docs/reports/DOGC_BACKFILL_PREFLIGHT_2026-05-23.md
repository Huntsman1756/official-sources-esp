# DOGC Backfill Preflight - 2026-05-23

## Scope

TASK-AUTO-DOGC-003-PREP prepared DOGC for a future controlled 30-day
metadata-only backfill.

Explicitly not performed:

- No VPS connection.
- No real DB backfill.
- No candidate creation.
- No artifact downloads.
- No downstream writes.
- No unrelated adapter changes.

## Files Inspected

- `src/official_sources/sources/dogc/client.py`
- `src/official_sources/sources/dogc/ingestion.py`
- `src/official_sources/sources/dogc/parser.py`
- `tests/test_dogc_adapter.py`
- `tests/test_cli_dogc.py`
- `docs/reports/DOGC_ADAPTER_MVP_LOCAL_2026-05-23.md`

## Local Temp DB Smoke

Smoke database:

```text
C:\Users\rome_\AppData\Local\Temp\dogc-preflight-20260523.sqlite
```

The smoke used the DOGC CLI entrypoint against local fixtures in a temporary
SQLite database. This verifies the command shape, repository writes, output
tokens, and schema validation without touching the VPS or downloading artifacts.

Published-date smoke:

```text
command_started=ingest-dogc-date source_code=DOGC target_date=2026-05-22
status=success issue_identifier=9671 documents_fetched=2 documents_new=1 documents_updated=1 retry_count=0 throttle_triggered=0 last_http_status=200 source_snapshot_hash=73c8468a49f30ba876f6dec6c485ab9ae2962c0298f4fc4d39f6d443a0a00fa7
```

No-publication smoke:

```text
command_started=ingest-dogc-date source_code=DOGC target_date=2026-05-23
status=no_publication issue_identifier=none documents_fetched=0 documents_new=0 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200 source_snapshot_hash=d991cc165c82731e4aea603d169b138b79a55f1ad01059e6dfbad3e2c0dc839b error_message=DOGC_returned_no_records_for_date_2026-05-23
```

DB validation:

```text
database_path=C:\Users\rome_\AppData\Local\Temp\dogc-preflight-20260523.sqlite current_version=8 latest_version=8 status=valid
EXIT_CODES published=0 no_publication=0 db_validate=0
```

Write-safety checks on the temp DB:

- `source_candidates`: `0`
- `artifact_download_attempts`: `0`
- `document_files`: one `raw_api_response` record only
- DOGC document rows preserve PDF/XML URLs as metadata only; no PDF/XML/HTML
  artifact file records are created.

## Live Local Probe

A local live CLI probe for `2026-05-22` was attempted against DOGC from this
workstation and failed before receiving an HTTP status:

```text
status=failed last_http_status=none error_message=[SSL:_SSLV3_ALERT_HANDSHAKE_FAILURE]_ssl/tls_alert_handshake_failure_(_ssl.c:1032)
```

This was not retried as a backfill and did not touch the VPS. Treat it as a
connectivity/TLS risk to verify on the VPS with a single-date smoke before any
30-day loop.

## Checks

Pagination and limit risk:

- `searchDOGC` payload is fixed at `page=1` and `numResultsByPage=100`.
- The adapter does not currently loop over additional pages.
- For a 30-day backfill, stop if any date appears to have more than 100
  documents or if DOGC response metadata indicates undiscovered pages.

Date search stability:

- The adapter validates ISO `YYYY-MM-DD`.
- `searchDOGC` receives `publicationDateInitial` and
  `publicationDateFinal` in `DD/MM/YYYY`.
- `calendarDOGC` is used before `searchDOGC` to preserve `numDOGC` when
  `hasDOGC=true`.
- Local fixture smoke is stable; live local TLS is not proven from this
  workstation.

Identifier stability:

- Date search records may only expose DOGC document IDs.
- Ingestion enriches each record through `documentDOGC` and normalizes final
  `external_id` to `DOGC:<CVE>`.
- Stop if `documentDOGC` omits `CVE`, returns mixed `numDOGC` values for a
  date, or returns metadata whose `dateDOGC` differs from the target date.

No-publication handling:

- Empty `resultSearch` is stored as `status=no_publication`.
- No documents, candidates, artifact download attempts, or artifact files are
  created for no-publication dates.
- The CLI output includes `source_snapshot_hash`, making future VPS reporting
  usable for both success and no-publication dates.

## Recommended VPS Command

Do not run a broad DOGC backfill until a fresh VPS backup and restore-copy
validation have passed. The current CLI has a one-date command, so the controlled
30-day operation should run as an explicit per-date loop, not as a hidden range
command.

Example future command shape:

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && \
  . /opt/official-sources/app/.venv/bin/activate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate && \
  for d in 2026-04-24 2026-04-25 2026-04-26 2026-04-27 2026-04-28 2026-04-29 2026-04-30 2026-05-01 2026-05-02 2026-05-03 2026-05-04 2026-05-05 2026-05-06 2026-05-07 2026-05-08 2026-05-09 2026-05-10 2026-05-11 2026-05-12 2026-05-13 2026-05-14 2026-05-15 2026-05-16 2026-05-17 2026-05-18 2026-05-19 2026-05-20 2026-05-21 2026-05-22 2026-05-23; do \
    official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-dogc-date --date \$d || exit 1; \
  done && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
```

Recommended pre/post VPS checks:

- Record `source_candidates` count before and after; it must not change.
- Record `artifact_download_attempts` count before and after; it must not
  change.
- Record `document_files` by `file_type`; DOGC should add only
  `raw_api_response` records.
- Record DOGC `ingestion_runs` by date with `status`, `documents_fetched`,
  `documents_new`, `documents_updated`, `last_http_status`, and
  `source_snapshot_hash`.

## Stop Conditions

Stop immediately if any of these occur:

- Any DOGC date returns `status=failed`.
- The VPS sees the same TLS handshake failure observed locally.
- `source_candidates` count changes.
- `artifact_download_attempts` count changes.
- Any DOGC `document_files.file_type` other than `raw_api_response` appears.
- `db validate` is not `status=valid` before or after the loop.
- A date appears paginated beyond page 1 / 100 results.
- `documentDOGC` returns missing `CVE`, mixed/missing `numDOGC`, or mismatched
  publication dates.
- Any command writes downstream exports or candidate/evidence review state.

## Test Decision

No tests were added. Existing focused tests already cover:

- DOGC date validation.
- Search payload date formatting.
- Published-date parsing.
- No-publication parsing.
- Metadata enrichment to CVE-backed external IDs.
- CLI success and no-publication output.
- No source candidates.
- No artifact download attempts.
- No PDF artifact file records.

The uncovered concern for a future 30-day backfill is not a small local test
gap; it is live DOGC pagination/connectivity behavior and should be verified by
a single-date VPS smoke plus guarded per-date execution.

## Readiness

DOGC is ready for a controlled VPS metadata-only backfill only after the future
operator completes the standard VPS backup/restore validation and a single-date
live smoke on the VPS succeeds. The adapter is not ready for unattended broad
historical backfill because pagination beyond the first 100 results is not
implemented and local live TLS was not proven from this workstation.

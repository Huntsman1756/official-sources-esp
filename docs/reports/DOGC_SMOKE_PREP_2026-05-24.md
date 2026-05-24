# DOGC VPS Smoke Prep - 2026-05-24

## Scope

Task: `TASK-AUTO-DOGC-SMOKE-PREP`.

This report prepares, but does not execute, a DOGC VPS smoke for one
published date and one no-publication date.

Explicitly not performed:

- No VPS connection.
- No ingestion run.
- No candidate creation.
- No artifact downloads.
- No downstream writes.

## Reviewed Inputs

- `src/official_sources/sources/dogc/client.py`
- `src/official_sources/sources/dogc/ingestion.py`
- `src/official_sources/sources/dogc/parser.py`
- `src/official_sources/cli.py`
- `tests/test_dogc_adapter.py`
- `tests/test_cli_dogc.py`
- `docs/reports/DOGC_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/DOGC_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/DOGC_CANDIDATE_DRY_RUN_PREFLIGHT_2026-05-23.md`
- `docs/reports/DOGC_VPS_SMOKE_RUNBOOK_2026-05-23.md`
- `docs/reports/NEXT_SOURCE_OPERATION_SYNTHESIS_2026-05-23.md`

## Adapter Summary

DOGC has a one-date metadata-only ingestion command:

```text
official-sources ingest-dogc-date --date YYYY-MM-DD
```

The command validates `YYYY-MM-DD`, calls `calendarDOGC` for the date issue
number when available, calls `searchDOGC` with exact publication-date bounds,
and enriches each search row through `documentDOGC`. Stored document external
IDs are normalized to `DOGC:<CVE>` after enrichment.

The adapter preserves official HTML, PDF, XML, RDF, and Turtle URLs as metadata
only. It should create only `raw_api_response` rows in `document_files`; it
should not create candidates, artifact download attempts, PDF/XML/HTML file
records, evidence-review state, or downstream exports.

## Suggested Smoke Dates

Use the dates already covered by DOGC fixtures and previous local preflight:

- Published date: `2026-05-22`.
- No-publication date: `2026-05-23`.

`2026-05-22` is the preferred first smoke because the fixture/preflight path
exercised document discovery, `documentDOGC` enrichment, issue identifier
handling, CVE-backed external IDs, and raw API response storage.

`2026-05-23` is the preferred second smoke because the fixture/preflight path
exercised controlled `status=no_publication` without creating documents,
candidates, artifact download attempts, or non-raw artifact file rows.

## Prepared Smoke Command

Do not run this from this task. This command is for the future VPS operator
after backup and restore-copy validation are recorded.

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && \
  . /opt/official-sources/app/.venv/bin/activate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-dogc-date --date 2026-05-22 && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
```

Expected published-date output shape:

- `command_started=ingest-dogc-date source_code=DOGC target_date=2026-05-22`
- `status=success`
- `last_http_status=200`
- `documents_fetched` is greater than `0` and less than `100`
- `issue_identifier` is present
- `source_snapshot_hash` is present
- stored DOGC `external_id` values are normalized as `DOGC:<CVE>`
- `source_candidates` count is unchanged
- `artifact_download_attempts` count is unchanged
- DOGC creates only `raw_api_response` rows in `document_files`

Run the no-publication smoke only after the published-date smoke succeeds and
the before/after safety checks are reviewed:

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && \
  . /opt/official-sources/app/.venv/bin/activate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-dogc-date --date 2026-05-23 && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
```

Expected no-publication output shape:

- `command_started=ingest-dogc-date source_code=DOGC target_date=2026-05-23`
- `status=no_publication`
- `documents_fetched=0`
- `documents_new=0`
- `documents_updated=0`
- `last_http_status=200`
- `source_snapshot_hash` is present
- no DOGC document rows are created for the date
- no candidate rows, artifact download attempts, or non-`raw_api_response`
  artifact file rows are created

Do not chain either smoke command to a 30-day loop.

## Risks To Verify

### TLS / Connectivity

The previous local live DOGC probe failed before an HTTP status with an SSL/TLS
handshake failure. This is the main reason the next operation must be a VPS
smoke rather than a backfill.

Stop on any TLS handshake failure, timeout, DNS failure, connection reset, or
non-200 DOGC HTTP status.

### Pagination

`searchDOGC` currently sends:

```text
page=1
numResultsByPage=100
```

The adapter does not fetch page 2 or reconcile total results. A 30-day backfill
is unsafe if any date can exceed the first-page ceiling.

Stop if the published-date smoke has `documents_fetched >= 100`, if a stored
payload exposes a total-result count above 100, or if DOGC metadata indicates
undiscovered pages.

### Date Search

The adapter uses `calendarDOGC` before `searchDOGC`, then searches with
`publicationDateInitial` and `publicationDateFinal` in `DD/MM/YYYY`.

Stop if `calendarDOGC` and `searchDOGC` disagree on publication presence or
issue identity, if `searchDOGC` returns records outside the target date, if
issue identifiers are mixed or missing, or if live DOGC changes the response
shape from the fixture assumptions.

### Identifiers

The stable stored identifier must be the DOGC CVE from `documentDOGC`; the DOGC
document ID is secondary lookup metadata.

Stop if `documentDOGC` omits `CVE`, returns a `dateDOGC` different from the
target date, returns mixed/missing `numDOGC` values for one date, causes two
records to collapse unexpectedly to the same CVE, or stores any DOGC
`external_id` that is not CVE-backed.

## Stop Conditions

Stop immediately and report without running a 30-day backfill if any of these
occur:

- Any DOGC command exits non-zero or reports `status=failed`.
- `db validate` is not `status=valid` before or after a command.
- TLS handshake failure, timeout, DNS failure, connection reset, or non-200
  DOGC HTTP status.
- `source_candidates` count changes.
- `artifact_download_attempts` count changes.
- DOGC creates any `document_files.file_type` other than `raw_api_response`.
- Any command downloads PDF, XML, RDF, Turtle, or HTML artifacts.
- Any command writes downstream exports, evidence-review state, approvals,
  publication files, or source candidates.
- The published smoke appears to require pagination beyond page 1 / 100
  results.
- `calendarDOGC` and `searchDOGC` disagree on publication presence or issue
  identity.
- `documentDOGC` omits `CVE`, returns mismatched dates, returns mixed/missing
  DOGC issue numbers, or fails to support CVE-backed external IDs.
- The future operator cannot explain the before/after database deltas.

## Criteria For Allowing A 30-Day Backfill

Allow a controlled 30-day DOGC metadata-only backfill only after all of these
criteria are met:

- A fresh VPS backup path is recorded.
- Restore-copy validation against that backup passes.
- Pre-smoke and post-smoke `db validate` both report `status=valid`.
- The `2026-05-22` published-date smoke succeeds on the VPS.
- The `2026-05-23` no-publication smoke succeeds on the VPS.
- The published-date smoke proves VPS connectivity with no TLS/connectivity
  issue and `last_http_status=200`.
- The published-date smoke remains below the first-page limit
  (`documents_fetched < 100`) and shows no pagination signal.
- Stored DOGC documents use CVE-backed `DOGC:<CVE>` external IDs.
- Pre/post counts prove no candidates, artifact download attempts, downstream
  writes, evidence-review state, or non-raw artifact files were created.
- The future operator uses an explicit visible per-date loop and stops on the
  first non-zero exit or stop-condition signal.

The backfill must remain metadata-only. It must not be combined with candidate
dry-runs, candidate writes, artifact downloads, downstream exports, or evidence
review operations.

## Recommendation

DOGC is ready only for the prepared VPS smoke sequence:

1. Published-date smoke for `2026-05-22`.
2. Review output, `db validate`, and safety-count deltas.
3. No-publication smoke for `2026-05-23`.
4. Review output, `db validate`, and safety-count deltas again.

DOGC is not ready for an unattended broad backfill. A 30-day metadata-only
backfill should be allowed only if both smoke dates pass and all stop
conditions remain clear.

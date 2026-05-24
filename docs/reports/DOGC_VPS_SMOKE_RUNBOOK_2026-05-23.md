# DOGC VPS Smoke Runbook - 2026-05-23

## Scope

Task: `TASK-AUTO-DOGC-003-RISK-RUNBOOK`.

This runbook prepares a cautious DOGC VPS smoke and 30-day metadata backfill
risk plan. It is documentation only.

Explicitly not performed in this task:

- No VPS connection.
- No ingestion run.
- No candidate creation.
- No artifact downloads.
- No downstream writes.
- No adapter or CLI changes.

## Reviewed Inputs

- `src/official_sources/sources/dogc/client.py`
- `src/official_sources/sources/dogc/ingestion.py`
- `src/official_sources/sources/dogc/parser.py`
- `docs/reports/DOGC_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/DOGC_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/DOGC_CANDIDATE_DRY_RUN_PREFLIGHT_2026-05-23.md`
- `docs/reports/PREFLIGHT_AND_BOPV_BACKFILL_INTEGRATION_2026-05-23.md`

## Known Risks

### TLS / Connectivity

The local live DOGC probe for `2026-05-22` failed before receiving an HTTP
status:

```text
[SSL:_SSLV3_ALERT_HANDSHAKE_FAILURE] ssl/tls alert handshake failure
```

Do not treat local fixture success as proof that the VPS can reach the DOGC
portal. The first VPS operation must be a single-date live smoke. A repeated
TLS handshake failure, timeout, or connection error is a stop condition.

### Pagination

`searchDOGC` currently sends:

```text
page=1
numResultsByPage=100
```

The adapter does not fetch page 2 or reconcile a total-result count. A 30-day
window is only acceptable while each date is visibly within the first-page
limit. Stop if any output, stored payload, or DOGC metadata indicates more than
100 results or undiscovered pages for a date.

### Date Search Stability

The adapter validates `YYYY-MM-DD`, asks `calendarDOGC` for the issue number,
then calls `searchDOGC` with exact `DD/MM/YYYY` publication-date bounds. This
is stable in fixtures, but not yet proven from the VPS against live DOGC.

Stop if `calendarDOGC` and `searchDOGC` disagree, if a date returns mixed or
missing issue identifiers, if `documentDOGC` returns metadata for a different
publication date, or if live DOGC changes the response shape.

### Identifier Stability

Date-search records may expose only DOGC document IDs. The ingestion path
enriches each row through `documentDOGC` and normalizes the final external ID to
`DOGC:<CVE>`.

The CVE is the stable identifier. The DOGC document ID is useful for lookup, but
must stay secondary. Stop if `documentDOGC` omits `CVE`, if two records collapse
to the same CVE unexpectedly, or if a stored `external_id` is not CVE-backed.

## Preconditions Before Any VPS Smoke

- A fresh VPS database backup exists and its path is recorded.
- A restore-copy validation has passed against that backup.
- `official-sources db validate` reports `status=valid` before the smoke.
- Baseline counts are recorded for `source_candidates`,
  `artifact_download_attempts`, and `document_files` by `file_type`.
- The operator is ready to stop after the one-date smoke even if it succeeds.

## One-Date VPS Smoke Command

This is the only DOGC live command allowed before deciding on a broader
metadata window. Use a known published date from the local preflight.

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && \
  . /opt/official-sources/app/.venv/bin/activate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-dogc-date --date 2026-05-22 && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
```

Expected smoke shape:

- `command_started=ingest-dogc-date source_code=DOGC target_date=2026-05-22`
- `status=success`
- `last_http_status=200`
- `documents_fetched` is greater than `0` and less than `100`
- `issue_identifier` is present
- `source_snapshot_hash` is present
- `source_candidates` count is unchanged
- `artifact_download_attempts` count is unchanged
- DOGC adds only `raw_api_response` rows to `document_files`

Do not chain this smoke to a 30-day loop. Review the output and database safety
checks first.

## No-Publication Test Command

Run this only after the published-date smoke succeeds. It verifies the empty-day
path without creating documents.

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && \
  . /opt/official-sources/app/.venv/bin/activate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-dogc-date --date 2026-05-23 && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
```

Expected no-publication shape:

- `status=no_publication`
- `documents_fetched=0`
- `documents_new=0`
- `documents_updated=0`
- `last_http_status=200`
- `source_snapshot_hash` is present
- No DOGC document rows, candidate rows, artifact download attempts, or
  non-`raw_api_response` artifact file rows are created by this run.

## Stop Conditions

Stop immediately and report without running a 30-day backfill if any of these
occur:

- TLS handshake failure, timeout, DNS failure, connection reset, or non-200 DOGC
  HTTP status.
- Any DOGC run ends with `status=failed`.
- `db validate` is not `status=valid` before or after a command.
- `source_candidates` count changes.
- `artifact_download_attempts` count changes.
- DOGC creates any `document_files.file_type` other than `raw_api_response`.
- Any command downloads PDF, XML, RDF, Turtle, or HTML artifacts.
- Any command writes downstream exports, evidence-review state, approvals, or
  publication files.
- A date appears to require pagination beyond page 1 / 100 results.
- `calendarDOGC` and `searchDOGC` disagree on publication presence or issue
  identity.
- `documentDOGC` omits `CVE`, returns a publication date different from the
  target date, or returns mixed/missing DOGC issue numbers.
- Stored DOGC `external_id` values are not normalized as `DOGC:<CVE>`.
- The operator cannot explain the before/after database deltas from the smoke.

## When A Full 30-Day Backfill Is Allowed

A controlled 30-day DOGC metadata-only backfill is allowed only after all of the
following are true:

- The one-date published smoke succeeds on the VPS.
- The no-publication test succeeds on the VPS.
- Fresh backup and restore-copy validation are recorded.
- Pre/post `db validate` is clean.
- Pre/post safety counts prove no candidates, artifact download attempts, or
  non-raw artifact files were created.
- The published-date smoke shows no TLS/connectivity issue.
- The smoke result is below the 100-result page ceiling.
- The stored DOGC documents use CVE-backed external IDs.
- The operator will execute an explicit per-date loop and stop on the first
  non-zero command exit or stop-condition signal.

The backfill must remain metadata-only. It must not be combined with candidate
dry-runs, candidate writes, artifact downloads, downstream exports, or evidence
review operations.

Use a visible per-date loop, not a hidden range command:

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && \
  . /opt/official-sources/app/.venv/bin/activate && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate && \
  for d in 2026-04-24 2026-04-25 2026-04-26 2026-04-27 2026-04-28 2026-04-29 2026-04-30 2026-05-01 2026-05-02 2026-05-03 2026-05-04 2026-05-05 2026-05-06 2026-05-07 2026-05-08 2026-05-09 2026-05-10 2026-05-11 2026-05-12 2026-05-13 2026-05-14 2026-05-15 2026-05-16 2026-05-17 2026-05-18 2026-05-19 2026-05-20 2026-05-21 2026-05-22 2026-05-23; do \
    official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-dogc-date --date \$d || exit 1; \
  done && \
  official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
```

## Reporting Requirements

The future operator should record:

- Backup path and restore-copy validation result.
- Exact smoke command output.
- `ingestion_runs` rows for DOGC smoke dates, including `status`,
  `documents_fetched`, `documents_new`, `documents_updated`,
  `last_http_status`, and `source_snapshot_hash`.
- Before/after counts for `source_candidates` and
  `artifact_download_attempts`.
- Before/after `document_files` counts grouped by `file_type`.
- Any observed pagination, date-search, or identifier anomaly.

## Readiness Decision

DOGC is not ready for an unattended broad backfill.

DOGC is ready only for a single-date VPS smoke under the stop conditions above.
A full 30-day metadata-only backfill is allowed only after the single-date
published smoke and the no-publication test both pass on the VPS and all safety
counts remain unchanged except for expected DOGC metadata/raw API response rows.

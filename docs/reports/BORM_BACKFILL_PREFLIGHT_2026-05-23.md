# BORM Backfill Preflight - 2026-05-23

## Scope

Task: `TASK-AUTO-BORM-003-PREP`.

This preflight prepares BORM for a future controlled 30-day metadata-only backfill.

Scope observed:

```text
local inspection only
temporary local SQLite smoke only
no VPS connection
no production database write
no real DB backfill
no source candidates
no downstream writes
no PDF/HTML/XML artifact downloads
no unrelated adapter changes
```

## Adapter Summary

BORM currently exposes a metadata-only CLI command:

```bash
official-sources --db-path <db> ingest-borm-date --date YYYY-MM-DD
```

The adapter fetches the official current-year XML index:

```text
https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml
```

It filters records where `Fec_Publicacion` starts with the requested `YYYY-MM-DD`.
For each matching record it stores official document metadata, preserves official HTML/PDF URLs as
metadata, stores the raw XML index snapshot as `raw_api_response`, and records an ingestion run.
It does not create source candidates or download PDF/HTML/XML artifacts.

## Local Temp DB Smoke

Temporary SQLite database was created under the local OS temp directory and removed after inspection.

Command class:

```bash
rtk proxy python -c "<temporary local smoke using official_sources.cli.run(...)>"
```

Published-date smoke:

```text
date=2026-05-20
command_started=ingest-borm-date source_code=BORM target_date=2026-05-20
status=success
issue_identifier=114/2026
documents_fetched=41
documents_new=41
documents_updated=0
retry_count=0
throttle_triggered=0
last_http_status=200
source_snapshot_hash=d2f96638601a2dc85de4a0f33fbc5b41c2e99247c89c1b4e62527a3271074b20
exit_code=0
```

No-publication smoke:

```text
date=2026-05-17
command_started=ingest-borm-date source_code=BORM target_date=2026-05-17
status=no_publication
issue_identifier=none
documents_fetched=0
documents_new=0
documents_updated=0
retry_count=0
throttle_triggered=0
last_http_status=200
source_snapshot_hash=d2f96638601a2dc85de4a0f33fbc5b41c2e99247c89c1b4e62527a3271074b20
error_message=BORM_returned_no_records_for_date_2026-05-17
exit_code=0
```

Database validation:

```text
valid=True
missing_tables=None
missing_columns=None
```

Temporary DB counts after both smoke dates:

```text
documents=41
candidates=0
artifact_attempts=0
pdf_files=0
raw_snapshots=41
runs=2
```

Ingestion run rows:

```text
BORM 2026-05-20 status=success documents_fetched=41 documents_new=41 documents_updated=0 last_http_status=200 error_message=None
BORM 2026-05-17 status=no_publication documents_fetched=0 documents_new=0 documents_updated=0 last_http_status=200 error_message="BORM returned no records for date 2026-05-17"
```

The `raw_snapshots=41` rows are expected `raw_api_response` metadata snapshots. They are not PDF,
HTML, or XML artifact downloads.

## Test Gap Decision

No new tests were added for this preflight.

Existing focused coverage already includes:

```text
date validation
source registration
published-date parsing
no-publication parsing
document metadata normalization
official URL preservation
raw payload hash preservation
metadata-only ingestion with no candidates
metadata-only ingestion with no artifact download attempts
CLI success output
CLI no-publication output
citation generation
```

The local smoke did not expose a clear low-risk gap that would justify code or test changes in this
prep task.

## Backfill Readiness Risks

Current-index strategy:

- Safe enough for a controlled 30-day current-year range, because the official current-year XML index
  contained both the published smoke date and the no-publication smoke date.
- Not safe as a general historical strategy beyond the current year. A future year-boundary or older
  historical backfill will likely need archived annual BORM index resources.
- Every date currently refetches the same current-year XML index and filters locally. This is simple
  and deterministic, but it duplicates network and storage work across dates.

Pagination/completeness:

- The discovered XML endpoint is a full current-year index, not a paginated API.
- There is no pagination cursor to follow and no reported total to reconcile.
- Stop if the XML shape changes, if expected current-year records disappear, or if a normal published
  weekday unexpectedly returns zero records without an official explanation.

No-publication behavior:

- Empty filtered record sets are treated as controlled `no_publication`.
- The smoke date `2026-05-17` returned `no_publication` with exit code `0`.
- Operators should still review weekend/holiday dates separately from unexpected weekday empties.

Timeout/connectivity:

- The local smoke reached the endpoint with `last_http_status=200`.
- The adapter uses an `httpx` timeout with `connect=10s` and `read=60s`.
- Stop on any non-200 response, timeout, parser failure, or repeated connection instability. Do not
  silently skip failed dates.

Artifact/candidate/downstream safety:

- Local smoke created no source candidates.
- Local smoke created no artifact download attempts.
- Local smoke created no PDF file rows.
- No downstream export path is involved in `ingest-borm-date`.

## Recommended Future VPS Command

Run BORM serially, one date at a time, after a fresh backup and DB validation. Do not chain candidate,
artifact, or downstream commands.

Recommended 30-day window for a task run on 2026-05-23:

```text
2026-04-24 through 2026-05-23 inclusive
```

Command pattern for the future VPS task:

```bash
OFFICIAL_SOURCES=/opt/official-sources/app/.venv/bin/official-sources
DB=/opt/official-sources/data/official_sources.sqlite
LOG=/opt/official-sources/logs/borm_30d_backfill_$(date -u +%Y%m%d_%H%M%S).log

$OFFICIAL_SOURCES --db-path "$DB" db validate

for d in $(python - <<'PY'
from datetime import date, timedelta
start = date.fromisoformat("2026-04-24")
for offset in range(30):
    print((start + timedelta(days=offset)).isoformat())
PY
); do
  echo "date=$d" | tee -a "$LOG"
  "$OFFICIAL_SOURCES" --db-path "$DB" ingest-borm-date --date "$d" 2>&1 | tee -a "$LOG"
  rc=${PIPESTATUS[0]}
  if [ "$rc" -ne 0 ]; then
    echo "stopped_on=$d exit_code=$rc" | tee -a "$LOG"
    exit "$rc"
  fi
  sleep 1
done

$OFFICIAL_SOURCES --db-path "$DB" db validate
```

Recommended pre-run checks:

```text
confirm no other VPS ingestion/candidate/downstream task is active
confirm fresh pre-run SQLite backup exists
confirm db validate is valid
confirm deployed commit includes BORM adapter and CLI
confirm command target is ingest-borm-date only
confirm date range is exactly 30 days
confirm no artifact downloader, candidate extraction, or downstream export command is chained
```

Recommended post-run checks:

```text
db validate returns valid
all 30 BORM ingestion_runs are success or no_publication
source_candidates count unchanged
artifact_download_attempts count unchanged
document_files file_type=pdf count unchanged for BORM
BORM document count for the range is plausible
no weekday no_publication appears without manual review
post-run SQLite backup is created only after DB validation passes
```

## Stop Conditions

Stop and report without continuing the range if any of these occur:

```text
db validate is invalid before the run
endpoint returns non-200 HTTP status
CLI command exits non-zero
status=failed
parser raises on XML shape or required field changes
mixed issue identifiers appear for one target date
documents_fetched=0 for a date expected to be published after manual calendar review
source_candidates count changes
artifact_download_attempts count changes
PDF/HTML/XML artifact download rows appear unexpectedly
downstream files or exports are touched
timeout/connectivity failures repeat for the same date
operator cannot reconcile BORM counts against the official web page for a sampled date
```

## Sequencing Decision

BORM is ready for a controlled metadata-only VPS backfill attempt, with the current-index limitation
documented.

Recommended order:

```text
1. BOPV/EHAA remains the preferred first autonomous backfill after integration.
2. BORM can be attempted before BOA and DOGC if the next slot is specifically choosing among those three.
3. Do not attempt BORM, BOA, and DOGC in parallel.
```

Reasoning:

- BORM local smoke is clean for both published and no-publication paths.
- BORM has no pagination cursor risk for the current-year 30-day window.
- The main BORM risk is historical/current-index scope, which is acceptable for a May 2026 30-day
  window but must block broader historical use.
- BOA and DOGC should remain separate serial tasks with their own preflight/backfill evidence.

## Decision

Proceed to a future supervised BORM VPS task only as a 30-day metadata-only run, after pre-run backup
and DB validation, and with the stop conditions above. Do not create candidates, do not download
artifacts, and do not touch downstream during that task.

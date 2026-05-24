# BORM 2026-05-11 Mixed Issue Diagnosis

Date: 2026-05-24

Task: `TASK-AUTO-BORM-004B`

Scope: diagnose and resolve the BORM ingestion failure for the single date `2026-05-11`.

No full backfill was resumed. No candidates were created. No PDF/XML/HTML artifacts were downloaded. No downstream project was touched.

## Context

`TASK-AUTO-BORM-004` stopped at the first failed date:

```text
target_date=2026-05-11
error=BORM response for 2026-05-11 has mixed issue identifiers
```

Previous partial state:

```text
dates_attempted=21
success=16
no_publication=4
failed=1
documents_fetched=311
documents_new=311
documents_updated=0
```

## Root Cause Classification

```text
supplement_issue
```

The official BORM XML index for `2026-05-11` contains two valid issue identifiers on the same publication date:

```text
106/2026 -> BOLETIN
2/2026   -> SUPLEMENTO
```

This is not a timeout, not a connectivity failure, and not wrong-date current-index leakage. The parser failed because it required exactly one issue identifier for every publication date.

## Official Response Observed

Safe diagnostic probe against:

```text
https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml
```

Observed:

```text
http_status=200
target_records=25
publication_date_counts=2026-05-11:25
issue_counts=106/2026:24,2/2026:1
publication_type_counts=BOLETIN:24,SUPLEMENTO:1
```

Document grouping:

| Issue identifier | Publication type | Documents |
| --- | --- | ---: |
| `106/2026` | `BOLETIN` | 24 |
| `2/2026` | `SUPLEMENTO` | 1 |

The supplement record has the same `Fec_Publicacion` date and its own BORM announcement identifiers and official URLs.

## Chosen Safe Behavior

The parser now accepts mixed issue identifiers only when the set is a same-date official BORM boletin plus supplement case:

```text
one BOLETIN issue identifier
one or more SUPLEMENTO issue identifiers
all records filtered to requested Fec_Publicacion date
publication types limited to BOLETIN/SUPLEMENTO
```

For that case:

```text
status=success
issue_identifier=comma-joined issue identifiers
issue_identifiers=list preserving official response order
each document keeps its own raw_metadata.issue_identifier
each document keeps raw_metadata.publication_type
```

Unsafe mixed cases still fail hard:

```text
two BOLETIN issue identifiers
unknown publication types
non-supplement mixed issue identifiers
```

Wrong-date current-index records remain filtered out by `Fec_Publicacion`.

## Code Changes

Changed:

```text
src/official_sources/sources/borm/parser.py
src/official_sources/sources/borm/ingestion.py
tests/test_borm_adapter.py
```

Behavior added:

- `BORMIssue.issue_identifiers` list.
- Narrow supplement-aware mixed issue handling.
- `ingest_borm_date()` returns `issue_identifiers` in the operational result.
- Existing document-level raw metadata continues to preserve the per-document `issue_identifier` and `publication_type`.

## Tests Added

Added coverage for:

- same-date boletin plus supplement issue succeeds;
- supplement document preserves `publication_type=SUPLEMENTO`;
- supplement document preserves `issue_identifier=2/2026`;
- two non-supplement BOLETIN issue identifiers still fail clearly;
- wrong-date/current-index records are filtered out;
- same-date supplement ingestion creates no candidates;
- same-date supplement ingestion creates no artifact download attempts;
- same-date supplement ingestion creates no PDF artifact rows.

Validation:

```text
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 422 passed, 1 warning
ruff check: passed
ruff format --check: passed
```

## Local Temp DB Smoke

Before touching the VPS DB again, the fixed code was run locally with a temporary SQLite DB and the official BORM XML endpoint.

Result:

```text
target_date=2026-05-11
status=success
issue_identifier=106/2026,2/2026
documents_fetched=25
documents_new=25
documents_updated=0
last_http_status=200
DB validation=status=valid schema_version=8
```

## VPS Deploy And Single-Date Smoke

Code commit deployed:

```text
d6a7e5c
```

Deploy command:

```bash
cd /opt/official-sources/app
git pull --ff-only origin main
. .venv/bin/activate
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Deployment note: `pip install -e .` emitted existing warnings for an invalid `~fficial-sources` distribution in the venv, but completed and the CLI DB validation passed.

Single-date smoke command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-borm-date --date 2026-05-11
```

Result:

```text
status=success
issue_identifier=106/2026,2/2026
documents_fetched=25
documents_new=25
documents_updated=0
retry_count=0
throttle_triggered=0
last_http_status=200
```

Latest stored BORM `2026-05-11` issue distribution:

```text
106/2026 BOLETIN: 24
2/2026 SUPLEMENTO: 1
```

## VPS Safety Verification

Post-smoke:

```text
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
BORM docs for 2026-05-11=25
BORM document_files_by_type=raw_api_response:336
DB validation=status=valid schema_version=8
MCP privacy=no matching official/mcp/python/uvicorn/fastmcp listeners
```

No PDF/XML/HTML artifacts were downloaded. No source candidates were created. No downstream writes were made.

Post-smoke backup:

```text
/opt/official-sources/data/backups/official_sources_after_borm_20260511_smoke_20260524_051124.sqlite
```

## Resume Decision

`2026-05-11` is now successfully ingested.

BORM backfill can resume from:

```text
2026-05-12
```

Recommended next task:

```text
TASK-AUTO-BORM-004C — Resume BORM 30-day metadata backfill
```

Scope:

```text
2026-05-12 -> 2026-05-20
metadata-only
serial one-date loop
stop on first failure
no candidates
no artifact downloads
no downstream
```

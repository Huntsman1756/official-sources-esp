# BORM 30-Day Metadata Backfill Resume

Date: 2026-05-24

Task: `TASK-AUTO-BORM-004C`

Scope: resume the controlled BORM metadata-only backfill after the validated supplement fix.

No candidates were created. No PDF/XML/HTML artifacts were downloaded. No downstream project was touched.

## Context

Previous BORM work:

```text
2026-04-21 -> 2026-05-10 ingested during BORM-004
2026-05-11 fixed and ingested during BORM-004B
```

This task resumed from:

```text
2026-05-12 -> 2026-05-20
```

## Deployed Commit

The VPS was updated from:

```text
d6a7e5c
```

to:

```text
1c9381a
```

The code fix was already present in `d6a7e5c`; the pull to `1c9381a` brought in the diagnosis report.

DB validation before the run:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

## Pre-Run State

```text
BORM official_documents=336
BORM ingestion_runs=22
BORM document_files_by_type=raw_api_response:336
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
```

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_borm_resume_20260524_051624.sqlite
```

## Resume Command

The run used a serial per-date loop for:

```text
2026-05-12 -> 2026-05-20
```

Command shape:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-borm-date --date YYYY-MM-DD
```

## Resume Result

```text
dates_processed=9
success=8
no_publication=1
failed=0
documents_fetched=213
documents_new=213
documents_updated=0
```

| Date | Status | Issue identifier | Fetched | New | Updated | HTTP | Retry | Throttle |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-05-12 | success | 107/2026 | 14 | 14 | 0 | 200 | 0 | 0 |
| 2026-05-13 | success | 108/2026 | 30 | 30 | 0 | 200 | 0 | 0 |
| 2026-05-14 | success | 109/2026 | 39 | 39 | 0 | 200 | 0 | 0 |
| 2026-05-15 | success | 110/2026,3/2026 | 15 | 15 | 0 | 200 | 0 | 0 |
| 2026-05-16 | success | 111/2026 | 30 | 30 | 0 | 200 | 0 | 0 |
| 2026-05-17 | no_publication | none | 0 | 0 | 0 | 200 | 0 | 0 |
| 2026-05-18 | success | 112/2026 | 27 | 27 | 0 | 200 | 0 | 0 |
| 2026-05-19 | success | 113/2026 | 17 | 17 | 0 | 200 | 0 | 0 |
| 2026-05-20 | success | 114/2026 | 41 | 41 | 0 | 200 | 0 | 0 |

## Supplement Issue Handling

The supplement-aware parser was exercised again during the resume:

```text
2026-05-15 -> 110/2026 BOLETIN + 3/2026 SUPLEMENTO
```

Supplement dates in the full 30-day window:

```text
2026-05-11: 2/2026 SUPLEMENTO, 1 document
2026-05-15: 3/2026 SUPLEMENTO, 2 documents
```

Both dates were ingested successfully while preserving document-level `issue_identifier` and `publication_type`.

## Final 30-Day Window Status

Final BORM window:

```text
2026-04-21 -> 2026-05-20
```

Latest run status by date:

```text
dates_total=30
success=25
no_publication=5
failed=0
documents_fetched=549
documents_new=549
documents_updated=0
```

Highest document-count dates:

```text
2026-05-20: 41
2026-05-14: 39
2026-05-13: 30
2026-05-16: 30
2026-05-18: 27
```

## Post-Run State

```text
BORM official_documents=549
BORM ingestion_runs=31
BORM document_files_by_type=raw_api_response:549
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
```

DB validation after the run:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_borm_resume_20260524_051756.sqlite
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listeners
```

## Safety Result

```text
source_candidates unchanged: 150 -> 150
artifact_download_attempts unchanged: 482 -> 482
artifact_bytes unchanged: 28857411 -> 28857411
PDF/XML/HTML artifact downloads: 0
downstream writes: 0
candidate writes: 0
```

Only BORM `raw_api_response` document files were created.

## Known Limitations

- This was metadata-only; no BORM evidence artifacts were downloaded.
- Candidate quality for BORM has not been measured yet.
- Supplement handling is intentionally narrow and only accepts official same-date `BOLETIN` + `SUPLEMENTO` cases.

## Next Recommended Task

```text
TASK-AUTO-BORM-005 — BORM candidate dry-run
```

Scope:

```text
source=BORM
range=2026-04-21 -> 2026-05-20
profile=borm-ayudas
dry-run only
no candidates
no artifact downloads
no downstream
```

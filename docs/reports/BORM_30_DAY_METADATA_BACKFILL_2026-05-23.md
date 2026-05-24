# BORM 30-Day Metadata Backfill

Date: 2026-05-24

Task: `TASK-AUTO-BORM-004`

Source: BORM - Boletin Oficial de la Region de Murcia

Target range:

```text
2026-04-21 -> 2026-05-20
```

Result: partial run stopped at the first failed date, as required by the runbook.

No candidates were created. No PDF/XML/HTML artifacts were downloaded. No downstream project was touched.

## Deployed Commit

The VPS was initially at:

```text
9557832
```

The VPS was fast-forwarded to:

```text
dfe6e65
```

Command used:

```bash
cd /opt/official-sources/app
git status --short
git rev-parse --short HEAD
git pull --ff-only origin main
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

DB validation result:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

## Pre-Run State

```text
BORM official_documents=0
BORM ingestion_runs=0
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
BORM document_files_by_type=[]
```

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_borm_30d_backfill_20260524_045531.sqlite
```

## Backfill Command

The run used the required serial one-date-at-a-time ingestion pattern:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-borm-date --date YYYY-MM-DD
```

The loop stopped on the first non-zero command exit.

## Dates Processed

```text
dates_attempted=21
success=16
no_publication=4
failed=1
not_attempted_after_stop=9
```

Attempted dates:

| Date | Status | Issue | Fetched | New | Updated | HTTP | Retry | Throttle | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2026-04-21 | success | 90/2026 | 16 | 16 | 0 | 200 | 0 | 0 |  |
| 2026-04-22 | success | 91/2026 | 23 | 23 | 0 | 200 | 0 | 0 |  |
| 2026-04-23 | success | 92/2026 | 12 | 12 | 0 | 200 | 0 | 0 |  |
| 2026-04-24 | success | 93/2026 | 22 | 22 | 0 | 200 | 0 | 0 |  |
| 2026-04-25 | success | 94/2026 | 26 | 26 | 0 | 200 | 0 | 0 |  |
| 2026-04-26 | no_publication | none | 0 | 0 | 0 | 200 | 0 | 0 | BORM returned no records for date. |
| 2026-04-27 | success | 95/2026 | 18 | 18 | 0 | 200 | 0 | 0 |  |
| 2026-04-28 | success | 96/2026 | 11 | 11 | 0 | 200 | 0 | 0 |  |
| 2026-04-29 | success | 97/2026 | 21 | 21 | 0 | 200 | 0 | 0 |  |
| 2026-04-30 | success | 98/2026 | 23 | 23 | 0 | 200 | 0 | 0 |  |
| 2026-05-01 | no_publication | none | 0 | 0 | 0 | 200 | 0 | 0 | BORM returned no records for date. |
| 2026-05-02 | success | 99/2026 | 16 | 16 | 0 | 200 | 0 | 0 |  |
| 2026-05-03 | no_publication | none | 0 | 0 | 0 | 200 | 0 | 0 | BORM returned no records for date. |
| 2026-05-04 | success | 100/2026 | 19 | 19 | 0 | 200 | 0 | 0 |  |
| 2026-05-05 | success | 101/2026 | 25 | 25 | 0 | 200 | 0 | 0 |  |
| 2026-05-06 | success | 102/2026 | 15 | 15 | 0 | 200 | 0 | 0 |  |
| 2026-05-07 | success | 103/2026 | 19 | 19 | 0 | 200 | 0 | 0 |  |
| 2026-05-08 | success | 104/2026 | 22 | 22 | 0 | 200 | 0 | 0 |  |
| 2026-05-09 | success | 105/2026 | 23 | 23 | 0 | 200 | 0 | 0 |  |
| 2026-05-10 | no_publication | none | 0 | 0 | 0 | 200 | 0 | 0 | BORM returned no records for date. |
| 2026-05-11 | failed | none | 0 | 0 | 0 | 200 | 0 | 0 | BORM response has mixed issue identifiers. |

Dates not attempted because the run stopped:

```text
2026-05-12
2026-05-13
2026-05-14
2026-05-15
2026-05-16
2026-05-17
2026-05-18
2026-05-19
2026-05-20
```

## Document Totals

```text
documents_fetched=311
documents_new=311
documents_updated=0
max_docs_single_day=26
```

Highest document-count dates:

```text
2026-04-25: 26
2026-05-05: 25
2026-04-22: 23
2026-04-30: 23
2026-05-09: 23
```

Sample external IDs:

```text
BORM:A-210426-1741
BORM:A-210426-1742
BORM:A-210426-1743
BORM:A-210426-1744
BORM:A-210426-1745
```

## Post-Run State

```text
BORM official_documents=311
BORM ingestion_runs=21
BORM document_files_by_type=raw_api_response:311
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
```

DB validation after the partial run:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_borm_30d_backfill_partial_20260524_045758.sqlite
```

MCP privacy check:

```bash
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

The only BORM file rows created were `raw_api_response` rows associated with metadata ingestion.

## Known Limitation

The run stopped at:

```text
2026-05-11
```

Failure:

```text
BORM response for 2026-05-11 has mixed issue identifiers
```

This should be treated as an adapter/data-shape issue before resuming the remaining dates. Do not rerun or skip the failed date without a specific follow-up task.

## Next Recommended Task

```text
TASK-AUTO-BORM-004B — Investigate BORM mixed issue identifiers on 2026-05-11
```

Recommended scope:

- inspect the stored failed `ingestion_runs` row;
- perform a safe live probe for `2026-05-11`;
- compare BORM issue/index records for that date;
- determine whether the adapter should split mixed issues, select the target issue, or fail hard;
- add fixture/test if the behavior is valid;
- only then decide whether to resume `2026-05-12 -> 2026-05-20`.

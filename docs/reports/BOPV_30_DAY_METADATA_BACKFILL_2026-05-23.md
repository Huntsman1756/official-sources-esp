# BOPV/EHAA 30-Day Metadata Backfill - 2026-05-23

## Scope

- VPS: `mcpspain-official-sources-vps` (`root@157.90.22.40`)
- App path: `/opt/official-sources/app`
- Database: `/opt/official-sources/data/official_sources.sqlite`
- Deployed commit: `c10ff19`
- Date range: `2026-04-21` through `2026-05-20`
- Command used per date: `official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-bopv-date --date <date>`

Only BOPV/EHAA metadata-by-date ingestion was run. No candidates, downstream writes, PDF/XML/HTML downloads, MCP exposure, or other source backfills were run.

## Pre-Run Checks

- Remote `git status --short`: clean
- Remote `git pull --ff-only origin main`: already up to date
- Remote DB validation before run: `status=valid`, schema version `8`

Pre-run counters:

| Metric | Before |
| --- | ---: |
| BOPV official_documents | 0 |
| BOPV ingestion_runs | 0 |
| source_candidates | 146 |
| artifact_download_attempts | 482 |
| `/opt/official-sources/data/artifacts` size | 28,857,411 bytes |

Pre-run backup:

- `/opt/official-sources/data/backups/official_sources_before_bopv_30d_backfill_20260523_202155.sqlite`
- Size: 58,413,056 bytes
- Verification: `quick_check`, `source_check=ok`, `backup_check=ok`, `status=success`

## Run Results

| Metric | Result |
| --- | ---: |
| Dates processed | 30 |
| Success dates | 20 |
| No-publication dates | 10 |
| Failed dates | 0 |
| Documents fetched | 489 |
| Documents new | 489 |
| Documents updated | 0 |

No-publication dates:

- `2026-04-25`
- `2026-04-26`
- `2026-04-28`
- `2026-05-01`
- `2026-05-02`
- `2026-05-03`
- `2026-05-09`
- `2026-05-10`
- `2026-05-16`
- `2026-05-17`

Issue identifiers fetched:

- `BOPV-2026-0073`
- `BOPV-2026-0074`
- `BOPV-2026-0075`
- `BOPV-2026-0076`
- `BOPV-2026-0077`
- `BOPV-2026-0078`
- `BOPV-2026-0079`
- `BOPV-2026-0080`
- `BOPV-2026-0081`
- `BOPV-2026-0082`
- `BOPV-2026-0083`
- `BOPV-2026-0084`
- `BOPV-2026-0085`
- `BOPV-2026-0086`
- `BOPV-2026-0087`
- `BOPV-2026-0088`
- `BOPV-2026-0089`
- `BOPV-2026-0090`
- `BOPV-2026-0091`
- `BOPV-2026-0092`
- `BOPV-2026-0093`

HTTP/retry summary:

- All processed dates returned `last_http_status=200`.
- `retry_count=0` for every date.
- `throttle_triggered=1` for all 20 success dates.
- `throttle_triggered=0` for all 10 no-publication dates.

## Post-Run Validation

- Remote DB validation after run: `status=valid`, schema version `8`

Post-run counters:

| Metric | Before | After | Changed |
| --- | ---: | ---: | --- |
| BOPV official_documents | 0 | 489 | Yes, expected metadata |
| BOPV ingestion_runs | 0 | 30 | Yes, expected run records |
| source_candidates | 146 | 146 | No |
| artifact_download_attempts | 482 | 482 | No |
| `/opt/official-sources/data/artifacts` size | 28,857,411 bytes | 28,857,411 bytes | No |

Artifact safety:

- `artifact_download_attempts` unchanged.
- `source_candidates` unchanged.
- Artifact directory size unchanged.
- No PDF/XML/HTML artifact downloads were triggered by this run.

MCP privacy check:

- Command: `ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true`
- Result: no matching listeners were returned.

Post-run backup:

- `/opt/official-sources/data/backups/official_sources_after_bopv_30d_backfill_20260523_202357.sqlite`
- Size: 59,338,752 bytes
- Verification: `quick_check`, `source_check=ok`, `backup_check=ok`, `status=success`

## Limitations

- This was metadata-only ingestion. It did not download, parse, or validate document body artifacts.
- No downstream candidate generation or publication flow was exercised.
- Existing artifact files in `/opt/official-sources/data/artifacts` were not audited beyond confirming counts/size safety for this run.

## Next Recommended Task

Start the BOPV candidate dry-run only after review of this report and confirmation that the metadata-only backfill counts are acceptable. The dry-run should remain candidate-only and must not write downstream publication artifacts unless explicitly approved.

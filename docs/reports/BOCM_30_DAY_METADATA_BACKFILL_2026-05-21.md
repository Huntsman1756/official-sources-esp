# BOCM 30-Day Metadata Backfill

Date: 2026-05-21

## Summary

`TASK-AUTO-BOCM-003` attempted a controlled metadata-only BOCM backfill for:

```text
2026-04-21 -> 2026-05-20
```

The run did not complete the full 30-day range. It stopped safely after a repeated read timeout
on `2026-04-22`, following the stop-on-failure rule.

No PDFs were downloaded. No candidates were created. No downstream project was touched.

## Deployed Commit

```text
0a9bee2 feat: add BOCM metadata adapter MVP
```

The VPS checkout was fast-forwarded to this commit before the backfill attempt.

## Commands Used

State and validation:

```bash
cd /opt/official-sources/app
git status --short
git rev-parse --short HEAD

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db status

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Backfill shape:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bocm-date --date YYYY-MM-DD
```

The dates were executed one at a time. The first pass stopped at `2026-04-22`. A single scoped
resume/retry from `2026-04-22` was attempted and failed with the same timeout. The remaining dates
were not processed.

## Backup Result

Pre-run backup:

```text
official_sources_before_bocm_30d_backfill_20260521_200158.sqlite
verification=quick_check
source_check=ok
backup_check=ok
status=success
```

Post-run backup:

```text
official_sources_after_bocm_30d_backfill_20260521_200654.sqlite
verification=quick_check
source_check=ok
backup_check=ok
status=success
```

## Pre/Post Counts

| metric | before | after |
| --- | ---: | ---: |
| BOCM official documents | 0 | 60 |
| BOCM ingestion runs | 0 | 3 |
| BOCM successful runs | 0 | 1 |
| BOCM no-publication runs | 0 | 0 |
| BOCM failed runs | 0 | 2 |
| BOCM PDF document files | 0 | 0 |
| artifact_download_attempts | 432 | 432 |
| source_candidates | 100 | 100 |
| artifact directory size | 26M | 26M |

## Date Results

| date | status | issue_identifier | documents_fetched | documents_new | documents_updated | last_http_status | note |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 2026-04-21 | success | bocm-20260421-93 | 60 | 60 | 0 | 200 | metadata stored |
| 2026-04-22 | failed | none | 0 | 0 | 0 | 200 | read timeout |
| 2026-04-22 | failed | none | 0 | 0 | 0 | 200 | single retry, read timeout |

Dates not processed because the controlled loop stopped on failure:

```text
2026-04-23 -> 2026-05-20
```

## HTTP Status Summary

```text
200: 3 ingestion attempts
```

Both failed attempts reached an HTTP 200 before timing out while reading the response.

## DB Validation

Post-run validation:

```text
status=valid
schema_version=8
```

## Artifact and Candidate Safety

The backfill remained metadata-only:

```text
BOCM PDF document_files: 0
artifact_download_attempts: 432 -> 432
source_candidates: 100 -> 100
artifacts: 26M -> 26M
```

No PDFs were downloaded. No candidate extraction was run. No downstream project was touched.

## MCP Privacy

The privacy check command returned no matching listener for:

```text
official|mcp|python|uvicorn|fastmcp
```

No public MCP listener or SQLite exposure was observed.

## Known Limitations

- The 30-day BOCM backfill is incomplete.
- `2026-04-22` timed out twice during official BOCM metadata retrieval.
- The adapter currently records read timeouts as failed ingestion runs and does not retry network
  read timeouts internally.
- The BOCM MVP remains metadata-only.
- No BOCM candidate dry-run should start until the range backfill reliability issue is resolved
  or the incomplete date is explicitly scoped and documented.

## Next Recommended Task

Recommended next task:

```text
TASK-AUTO-BOCM-003B — Harden BOCM metadata backfill against read timeouts
```

Scope should remain narrow:

```text
diagnose 2026-04-22 timeout
avoid broad crawling
metadata only
no PDFs
no candidates
no downstream
```

After that, rerun the controlled BOCM 30-day metadata backfill from the failed date.

Follow-up status:

```text
TASK-AUTO-BOCM-003B implemented timeout hardening in code.
docs/reports/BOCM_TIMEOUT_HARDENING_2026-05-21.md records the retry strategy and smoke result.
```

# BOJA 30-Day Metadata Backfill Resume - 2026-05-20

## Summary

TASK-AUTO-003C resumed the controlled BOJA metadata-only 30-day backfill after TASK-AUTO-003B hardened BOJA no-publication handling.

The original 30-day target window is now complete at the metadata layer:

```text
2026-04-21 to 2026-05-20
```

No PDFs, HTML/XML artifacts, candidates, downstream writes, approvals, publications, MCP exposure, BOE tasks, broader BOJA ranges, or additional autonomous adapters were run.

## Deployed State

VPS application path:

```text
/opt/official-sources/app
```

Deployed commit after fast-forward pull:

```text
c5d0c01
```

Database status before resume:

```text
current_version=8
latest_version=8
journal_mode=wal
synchronous=2
status=valid
```

The VPS started at `d579eda` and was updated to `c5d0c01` with a fast-forward pull. Editable reinstall completed; the virtual environment still emitted pre-existing `Ignoring invalid distribution ~fficial-sources` warnings, but the CLI ran successfully.

## Resume Range

Resume range:

```text
2026-04-25 to 2026-05-20
```

Previously completed dates were not rerun:

```text
2026-04-21 to 2026-04-24
```

## Pre-Run State

Before resume:

```text
BOJA official_documents: 225
BOJA ingestion_runs: 5
artifact_download_attempts: 392
artifact directory size: 24M
```

Existing BOJA documents:

| date | documents |
| --- | ---: |
| 2026-04-21 | 62 |
| 2026-04-22 | 42 |
| 2026-04-23 | 47 |
| 2026-04-24 | 74 |

Existing BOJA runs included one failed run for `2026-04-25` from TASK-AUTO-003 before BOJA HTTP 400 no-publication behavior was hardened.

## Pre-Run Backup

Pre-resume backup:

```text
official_sources_before_boja_resume_20260520_153705.sqlite
size_bytes=46067712
size_mb=43.93
status=success
```

## Command Executed

The resume used one date at a time:

```bash
for d in $(python3 - <<'PY'
from datetime import date, timedelta
start = date.fromisoformat("2026-04-25")
end = date.fromisoformat("2026-05-20")
cur = start
while cur <= end:
    print(cur.isoformat())
    cur += timedelta(days=1)
PY
); do
  echo "== BOJA $d =="
  /opt/official-sources/app/.venv/bin/official-sources \
    --db-path /opt/official-sources/data/official_sources.sqlite \
    ingest-boja-date --date "$d"
  sleep 1
done
```

## Resume Result

Per-date result:

| date | status | pages_fetched | pagination_complete | documents_fetched | documents_new | documents_updated | last_http_status |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2026-04-25 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-04-26 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-04-27 | success | 1 | true | 44 | 44 | 0 | 200 |
| 2026-04-28 | success | 1 | true | 66 | 66 | 0 | 200 |
| 2026-04-29 | success | 1 | true | 85 | 85 | 0 | 200 |
| 2026-04-30 | success | 1 | true | 79 | 79 | 0 | 200 |
| 2026-05-01 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-02 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-03 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-04 | success | 1 | true | 98 | 98 | 0 | 200 |
| 2026-05-05 | success | 1 | true | 84 | 84 | 0 | 200 |
| 2026-05-06 | success | 1 | true | 92 | 92 | 0 | 200 |
| 2026-05-07 | success | 1 | true | 83 | 83 | 0 | 200 |
| 2026-05-08 | success | 1 | true | 95 | 95 | 0 | 200 |
| 2026-05-09 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-10 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-11 | success | 1 | true | 63 | 63 | 0 | 200 |
| 2026-05-12 | success | 1 | true | 78 | 78 | 0 | 200 |
| 2026-05-13 | success | 1 | true | 58 | 58 | 0 | 200 |
| 2026-05-14 | success | 1 | true | 87 | 87 | 0 | 200 |
| 2026-05-15 | success | 1 | true | 69 | 69 | 0 | 200 |
| 2026-05-16 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-17 | no_publication | 0 | true | 0 | 0 | 0 | 400 |
| 2026-05-18 | success | 1 | true | 60 | 60 | 0 | 200 |
| 2026-05-19 | success | 1 | true | 72 | 72 | 0 | 200 |
| 2026-05-20 | success | 1 | true | 62 | 62 | 0 | 200 |

Resume totals:

```text
dates_processed=26
success_dates=17
no_publication_dates=9
failed_dates=0
documents_fetched=1275
documents_new=1275
documents_updated=0
pages_fetched_total=17
pagination_complete_dates=26
http_200_dates=17
http_400_no_publication_dates=9
```

## Original 30-Day Window Final State

For the original full range:

```text
2026-04-21 to 2026-05-20
```

Latest status distribution:

```text
success=21
no_publication=9
failed=0
```

BOJA metadata totals after resume:

```text
BOJA official_documents: 1500
BOJA ingestion_runs: 31
```

The run count is 31 because `2026-04-25` has the original failed run from TASK-AUTO-003 plus the newer successful `no_publication` run from TASK-AUTO-003C.

## Selected Status Checks

| date | BOJA documents | latest status | documents_fetched | documents_new | documents_updated | last_http_status |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2026-04-25 | 0 | no_publication | 0 | 0 | 0 | 400 |
| 2026-04-27 | 44 | success | 44 | 44 | 0 | 200 |
| 2026-05-01 | 0 | no_publication | 0 | 0 | 0 | 400 |
| 2026-05-19 | 72 | success | 72 | 72 | 0 | 200 |
| 2026-05-20 | 62 | success | 62 | 62 | 0 | 200 |

## Artifact Checks

Artifacts before/after:

```text
artifact directory size before: 24M
artifact directory size after: 24M
artifact_download_attempts before: 392
artifact_download_attempts after: 392
```

No artifact download command was run.

## DB Validation

Post-resume database validation:

```text
current_version=8
latest_version=8
status=valid
```

## MCP Privacy

The listener check returned no `official`, `mcp`, `python`, `uvicorn`, or `fastmcp` process.

Result:

```text
no public MCP listener observed
no SQLite exposure observed
```

## Post-Run Backup

Post-resume backup:

```text
official_sources_after_boja_resume_20260520_153959.sqlite
size_bytes=48959488
size_mb=46.69
status=success
```

## Known Limitations

- BOJA still has no native range command; this resume used a conservative shell loop.
- BOJA no-publication HTTP 400 handling is intentionally narrow and only covers the observed generic JSON body.
- No BOJA candidates exist yet.
- No BOJA PDF download, HTML/XML artifact download, text extraction, downstream export, or downstream integration exists yet.
- The VPS virtual environment still emits pre-existing `Ignoring invalid distribution ~fficial-sources` warnings during editable install.

## Recommendation

The controlled BOJA 30-day metadata window is complete.

Recommended next task:

```text
TASK-AUTO-004 - BOJA candidate dry-run
```

Scope:

- dry-run only;
- use stored BOJA metadata;
- no BOJA API calls;
- no candidate writes;
- no PDFs;
- no downstream writes.

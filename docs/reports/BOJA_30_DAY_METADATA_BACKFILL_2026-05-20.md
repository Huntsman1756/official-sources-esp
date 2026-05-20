# BOJA 30-Day Metadata Backfill - 2026-05-20

## Summary

TASK-AUTO-003 attempted a controlled BOJA 30-day metadata-only backfill on the deployed `official-sources` VPS.

The run was intentionally stopped on the first ambiguous failure. It did not complete the full 30-day range because BOJA returned HTTP 400 for `2026-04-25`.

No PDFs, HTML/XML artifacts, candidates, downstream writes, approvals, publications, MCP exposure, BOE tasks, or additional autonomous adapters were run.

## Deployed State

VPS application path:

```text
/opt/official-sources/app
```

Deployed commit after fast-forward pull:

```text
d579eda
```

Database status before the run:

```text
current_version=8
latest_version=8
status=valid
```

The VPS started behind `main` at `f0db289`; it was updated with:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
python -m pip install -e .
```

`pip install -e .` completed. It emitted pre-existing `Ignoring invalid distribution ~fficial-sources` warnings in the virtual environment, but the installed CLI responded and the backfill command ran.

## Target Range

Requested inclusive range:

```text
2026-04-21 to 2026-05-20
```

Actual processing stopped at:

```text
2026-04-25
```

## Pre-Run Counts

Before the run:

```text
BOJA official_documents: 0
BOJA ingestion_runs: 0
artifact_download_attempts: 392
artifact directory size: 24M
```

## Pre-Run Backup

Pre-run backup:

```text
official_sources_before_boja_30d_backfill_20260520_152436.sqlite
size_bytes=45555712
size_mb=43.45
status=success
```

The backup command completed successfully before any BOJA metadata ingestion.

## Command Executed

The safe backfill used one date at a time:

```bash
for d in $(python3 - <<'PY'
from datetime import date, timedelta
start = date.fromisoformat("2026-04-21")
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

The first local SSH quoting attempt failed before any date was processed and before any ingestion command ran. The command above was then sent through stdin to `bash` and is the command that performed the writes.

## Run Result

Per-date result:

| date | status | pages_fetched | pagination_complete | documents_fetched | documents_new | documents_updated | last_http_status |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 2026-04-21 | success | 1 | true | 62 | 62 | 0 | 200 |
| 2026-04-22 | success | 1 | true | 42 | 42 | 0 | 200 |
| 2026-04-23 | success | 1 | true | 47 | 47 | 0 | 200 |
| 2026-04-24 | success | 1 | true | 74 | 74 | 0 | 200 |
| 2026-04-25 | failed | 0 | false | 0 | 0 | 0 | 400 |

Totals:

```text
dates_attempted=5
success_dates=4
no_publication_dates=0
failed_dates=1
documents_fetched=225
documents_new=225
documents_updated=0
pages_fetched_total=4
pagination_complete_success_dates=4
pagination_incomplete_or_failed_dates=1
```

The run stopped correctly after the first failed date and did not continue through the remaining dates.

## Failure

Failed date:

```text
2026-04-25
```

Observed result:

```text
status=failed
last_http_status=400
pagination_complete=false
documents_fetched=0
```

The adapter recorded the HTTP 400 as a failed ingestion run. This was the correct conservative behavior at the time because BOJA no-publication semantics for HTTP 400 had not yet been defined or fixture-covered.

TASK-AUTO-003B later confirmed that BOJA uses this exact generic JSON 400 body for valid no-publication dates and added a narrow tested classifier. Do not reinterpret other BOJA HTTP 400 bodies as `no_publication`.

## Selected Status Checks

Selected date checks after the stopped run:

| date | BOJA documents | ingestion run |
| --- | ---: | --- |
| 2026-04-21 | 62 | success |
| 2026-05-05 | 0 | not reached |
| 2026-05-20 | 0 | not reached |

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

Post-run database validation:

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

Post-run backup:

```text
official_sources_after_boja_30d_backfill_20260520_152610.sqlite
size_bytes=46067712
size_mb=43.93
status=success
```

The post-run backup was created because the database remained valid and the run wrote four successful BOJA dates before stopping.

## Known Limitations

- The requested 30-day range was not completed.
- BOJA returned HTTP 400 for `2026-04-25`; TASK-AUTO-003B now classifies only the observed generic BOJA 400 body as `no_publication`.
- BOJA HTTP 400/no-publication semantics are now documented and fixture-covered for the observed body only.
- The VPS virtual environment still emits pre-existing `Ignoring invalid distribution ~fficial-sources` warnings during editable install.
- No BOJA range command exists yet; the run used a conservative shell loop.
- No BOJA candidate extraction exists yet.
- No BOJA PDF download, text extraction, downstream export, or downstream integration exists yet.

## Recommendation

Do not start BOJA candidate dry-run yet.

Recommended next task:

```text
TASK-AUTO-003C - Resume controlled BOJA 30-day metadata backfill
```

Scope:

- deploy the BOJA no-publication hardening commit to the VPS;
- resume from `2026-04-25` through `2026-05-20`;
- keep metadata-only behavior;
- no PDFs;
- no candidates;
- no downstream.

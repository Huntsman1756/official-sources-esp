# BOA Backfill Preflight - 2026-05-23

## Scope

Task: `TASK-AUTO-BOA-003-PREP`.

This is a local preflight for a future BOA 30-day metadata-only backfill.

Rules applied:

- No VPS connection.
- No real DB backfill.
- No source candidates.
- No artifact downloads.
- No downstream writes.
- No unrelated adapter changes.

## Adapter Surface Reviewed

Reviewed paths:

- `src/official_sources/sources/boa/client.py`
- `src/official_sources/sources/boa/parser.py`
- `src/official_sources/sources/boa/ingestion.py`
- `tests/test_boa_adapter.py`
- `tests/test_cli_boa.py`
- `docs/reports/BOA_ADAPTER_MVP_LOCAL_2026-05-23.md`

The BOA adapter is scoped to one-date metadata ingestion through:

```text
official-sources ingest-boa-date --date YYYY-MM-DD
```

The client uses the official BOA CGI JSON endpoint:

```text
https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VERLST&BASE=BOLE&DOCS=1-250&SEC=OPENDATABOAJSONAPP&OUTPUTMODE=JSON&SORT=-PUBL&SEPARADOR=&PUBL=YYYYMMDD
```

## Local Temp DB Smoke

Smoke database:

```text
C:\Users\rome_\AppData\Local\Temp\boa-preflight-20260523.sqlite
```

Published-date command:

```powershell
rtk powershell -NoProfile -Command "`$env:PYTHONPATH='src'; python -c 'from official_sources.cli import main; main()' --db-path C:\Users\rome_\AppData\Local\Temp\boa-preflight-20260523.sqlite ingest-boa-date --date 2026-01-28"
```

Output:

```text
command_started=ingest-boa-date source_code=BOA target_date=2026-01-28
status=success issue_identifier=18/2026 documents_fetched=54 documents_new=54 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200 source_snapshot_hash=acebb7e701acfa770654fe974e1bae00cf14298e13825874c6532ecc00b723bf
```

No-publication command:

```powershell
rtk powershell -NoProfile -Command "`$env:PYTHONPATH='src'; python -c 'from official_sources.cli import main; main()' --db-path C:\Users\rome_\AppData\Local\Temp\boa-preflight-20260523.sqlite ingest-boa-date --date 2026-01-25"
```

Output:

```text
command_started=ingest-boa-date source_code=BOA target_date=2026-01-25
status=no_publication issue_identifier=none documents_fetched=0 documents_new=0 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200 source_snapshot_hash=eb487fa63eb7026e41993bf01995379167ce2d49f9f72ba9b6282e3bed5da834 error_message=BOA_returned_no_records_for_date_2026-01-25
```

## Temp DB Validation

Command:

```powershell
rtk powershell -NoProfile -Command "`$env:PYTHONPATH='src'; python -c 'from official_sources.cli import main; main()' --db-path C:\Users\rome_\AppData\Local\Temp\boa-preflight-20260523.sqlite db validate"
```

Output:

```text
database_path=C:\Users\rome_\AppData\Local\Temp\boa-preflight-20260523.sqlite current_version=8 latest_version=8 status=valid
```

Temp DB checks:

```text
official_documents=count:54
source_candidates=count:0
artifact_download_attempts=count:0
document_files_total=count:54
document_files_by_type=file_type:raw_api_response,count:54
runs=source_code:BOA,target_date:2026-01-25,status:no_publication,documents_fetched:0,documents_new:0,documents_updated:0,last_http_status:200;source_code:BOA,target_date:2026-01-28,status:success,documents_fetched:54,documents_new:54,documents_updated:0,last_http_status:200
```

No `data/` files were created in the worktree during the smoke.

## CLI Report Readiness

The `ingest-boa-date` CLI output includes enough fields for a future VPS report:

- `target_date`
- `status`
- `issue_identifier`
- `documents_fetched`
- `documents_new`
- `documents_updated`
- `retry_count`
- `throttle_triggered`
- `last_http_status`
- `source_snapshot_hash`
- compact `error_message` for no-publication or failure paths

These fields are sufficient to summarize processed dates, success/no-publication/failure counts, document totals, HTTP status distribution, retry/throttle signals, issue identifiers, and source snapshot integrity.

## Pagination And Limit Risk

Current BOA date URL requests `DOCS=1-250`.

Preflight finding:

- The live published-date smoke for `2026-01-28` returned `54` documents, well below the `250` limit.
- The parser treats the returned JSON array as complete and does not inspect a total-count field.
- The endpoint strategy does not currently paginate beyond `DOCS=1-250`.

Risk:

- Low for normal daily issues based on the smoke and the adapter MVP report, but not zero. A very large issue could silently truncate if BOA returns only the requested `DOCS` window and no explicit overflow signal.

Recommended guard for the VPS run:

- Treat any date with `documents_fetched=250` as a stop condition requiring manual pagination review before continuing.

## Tests

No tests were added in this preflight.

Reason:

- Existing BOA tests already cover date validation, source registration, published-date parsing, no-publication parsing, metadata normalization, URL preservation, metadata-only ingestion, zero source candidates, zero artifact download attempts, citation generation, and CLI success/no-publication output.
- No clear low-risk gap was found that would improve this preflight without changing scope.

## Recommended VPS Command

Do not run until explicitly approved for the VPS backfill.

Recommended pattern for a controlled 30-day metadata-only run:

```bash
cd /opt/official-sources/app
for d in $(python - <<'PY'
from datetime import date, timedelta
end = date.today()
start = end - timedelta(days=29)
current = start
while current <= end:
    print(current.isoformat())
    current += timedelta(days=1)
PY
); do
  /opt/official-sources/app/.venv/bin/official-sources \
    --db-path /opt/official-sources/data/official_sources.sqlite \
    ingest-boa-date --date "$d"
  sleep 1
done | tee /opt/official-sources/logs/boa_30d_backfill_$(date +%Y%m%d_%H%M).log
```

Before running on VPS:

- Confirm deployed commit contains the BOA adapter and this preflight report.
- Confirm `/opt/official-sources/app/.venv/bin/official-sources --help` includes `ingest-boa-date`.
- Confirm a database backup exists.
- Run one current no-publication or low-risk date first if an operator wants a final live check.

## Stop Conditions

Stop the future VPS run if any of these occur:

- Any command exits non-zero.
- `status=failed`.
- `last_http_status` is not `200`.
- `source_snapshot_hash=none`.
- `documents_fetched=250`.
- `retry_count` is greater than `0` on repeated dates.
- `throttle_triggered` is non-zero.
- Candidate count increases after BOA ingestion.
- Artifact download attempt count increases after BOA ingestion.
- Any non-`raw_api_response` file rows are created by BOA ingestion.
- Database validation fails after the run.

## Readiness

BOA is ready for an explicitly approved VPS metadata-only 30-day backfill with the stop conditions above.


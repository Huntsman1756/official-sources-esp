# BOCM 2026-05-06 Single-Date Retry

Date: 2026-05-21

## Summary

`TASK-AUTO-BOCM-003F` retried BOCM ingestion for:

```text
2026-05-06
```

This was a single-date operational retry after cooldown. No broad backfill was run.

Result:

```text
date_recovered=false
```

No PDFs were downloaded. No candidates were created. No downstream project was touched.

## VPS State

```text
commit=1ef86aa
DB validation before retry=valid
```

## Connectivity Probe

Command shape:

```bash
curl -I --max-time 20 https://www.bocm.es/
```

Result:

```text
status=200
total=0.126428
connect=0.036009
starttransfer=0.126280
remote_ip=195.77.128.44
http_version=1.1
content_type=text/html; charset=utf-8
```

The BOCM home page was reachable from the VPS at retry time.

## Ingest Retry

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bocm-date --date 2026-05-06
```

Result:

```text
status=failed
issue_identifier=none
documents_fetched=0
documents_new=0
documents_updated=0
retry_count=3
throttle_triggered=1
last_http_status=none
source_snapshot_hash=none
error_message=BOCM_search_day_request_for_2026-05-06_timed_out_after_4_attempts:_timed_out
```

The retry remained a `search_day` timeout. It was correctly not classified as `no_publication`.

## Post-Retry Validation

```text
DB validation=valid
```

Safety counts:

```text
BOCM official_documents=982
BOCM PDF document_files=0
artifact_download_attempts=432
source_candidates=100
```

## Backfill Decision

The BOCM 30-day metadata backfill cannot resume yet.

Reason:

```text
2026-05-06 still fails from the VPS after controlled single-date retry.
```

Do not run:

```text
BOCM candidate dry-run
BOCM PDF download
BOCM downstream writes
```

## Next Recommended Step

Keep BOCM paused unless a later cooldown retry succeeds.

Reasonable next options:

```text
1. Wait and retry 2026-05-06 once later from the VPS.
2. If repeated failures persist, document BOCM as externally blocked from this VPS path.
3. Move to a separate source audit, such as DOGV, without touching BOCM candidates.
```

Do not start BOCM candidate work until the metadata-only window is complete or the blocker is
explicitly accepted.

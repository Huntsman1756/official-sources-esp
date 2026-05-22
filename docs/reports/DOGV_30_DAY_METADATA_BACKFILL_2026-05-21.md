# DOGV 30-Day Metadata Backfill

Date: 2026-05-21

## Summary

TASK-AUTO-DOGV-003 ran a controlled DOGV metadata-only backfill on the VPS for the
range 2026-04-21 through 2026-05-20.

The backfill completed the full 30-day window without failures.

No PDF, XML, or HTML artifacts were downloaded. No source candidates were created. No
downstream writes, approvals, or publications were performed.

## Deployed Code

```text
deployed_commit=7f1f1ec
repository=/opt/official-sources/app
database=/opt/official-sources/data/official_sources.sqlite
```

The deployed commit includes the DOGV metadata adapter MVP and the
`official-sources ingest-dogv-date --date YYYY-MM-DD` CLI command.

## Commands Used

Pre-run validation:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Pre-run backup:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_before_dogv_30d_backfill_20260522_054711.sqlite
```

Backfill loop:

```bash
for d in 2026-04-21 ... 2026-05-20; do
  /opt/official-sources/app/.venv/bin/official-sources \
    --db-path /opt/official-sources/data/official_sources.sqlite \
    ingest-dogv-date --date "$d"
  sleep 1
done
```

Post-run validation:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Post-run backup:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_after_dogv_30d_backfill_20260522_054936.sqlite
```

## Date Results

```text
date_range=2026-04-21 -> 2026-05-20
dates_processed=30
success=21
no_publication=9
failed=0
http_status_summary=200:30
retry_count_total=0
```

Successful dates:

```text
2026-04-21
2026-04-22
2026-04-23
2026-04-24
2026-04-27
2026-04-28
2026-04-29
2026-04-30
2026-05-04
2026-05-05
2026-05-06
2026-05-07
2026-05-08
2026-05-11
2026-05-12
2026-05-13
2026-05-14
2026-05-15
2026-05-18
2026-05-19
2026-05-20
```

No-publication dates:

```text
2026-04-25
2026-04-26
2026-05-01
2026-05-02
2026-05-03
2026-05-09
2026-05-10
2026-05-16
2026-05-17
```

Failed dates:

```text
none
```

## Issue Identifiers

```text
2026-04-21 -> 10346
2026-04-22 -> 10347
2026-04-23 -> 10348
2026-04-24 -> 10349
2026-04-27 -> 10350
2026-04-28 -> 10351
2026-04-29 -> 10352
2026-04-30 -> 10353
2026-05-04 -> 10354
2026-05-05 -> 10355
2026-05-06 -> 10356
2026-05-07 -> 10357
2026-05-08 -> 10358
2026-05-11 -> 10359
2026-05-12 -> 10360
2026-05-13 -> 10361
2026-05-14 -> 10362
2026-05-15 -> 10363
2026-05-18 -> 10364
2026-05-19 -> 10365
2026-05-20 -> 10366
```

## Document Counts

```text
documents_fetched=1113
documents_new=1113
documents_updated=0
DOGV_official_documents_before=0
DOGV_official_documents_after=1113
DOGV_ingestion_runs_before=0
DOGV_ingestion_runs_after=30
```

Per-date document counts:

```text
2026-04-21: 80
2026-04-22: 52
2026-04-23: 52
2026-04-24: 48
2026-04-25: 0
2026-04-26: 0
2026-04-27: 69
2026-04-28: 74
2026-04-29: 50
2026-04-30: 65
2026-05-01: 0
2026-05-02: 0
2026-05-03: 0
2026-05-04: 1
2026-05-05: 39
2026-05-06: 68
2026-05-07: 46
2026-05-08: 48
2026-05-09: 0
2026-05-10: 0
2026-05-11: 63
2026-05-12: 71
2026-05-13: 43
2026-05-14: 80
2026-05-15: 1
2026-05-16: 0
2026-05-17: 0
2026-05-18: 70
2026-05-19: 44
2026-05-20: 49
```

## Safety Checks

```text
artifact_directory_size_before=26M
artifact_directory_size_after=26M
artifact_download_attempts_before=432
artifact_download_attempts_after=432
source_candidates_before=100
source_candidates_after=100
db_validation_before=valid
db_validation_after=valid
MCP_privacy=no matching public listener observed
```

The unchanged artifact directory size and unchanged artifact download attempt count confirm that
the run remained metadata-only.

## Backups

Pre-run backup:

```text
path=/opt/official-sources/data/backups/official_sources_before_dogv_30d_backfill_20260522_054711.sqlite
verification=quick_check
source_check=ok
backup_check=ok
status=success
size_bytes=51269632
```

Post-run backup:

```text
path=/opt/official-sources/data/backups/official_sources_after_dogv_30d_backfill_20260522_054936.sqlite
verification=quick_check
source_check=ok
backup_check=ok
status=success
size_bytes=54632448
```

## Known Limitations

This run is metadata-only. It preserves official DOGV URL metadata but does not download or review
HTML, XML, or PDF artifacts.

No candidate extraction was run, so DOGV relevance for downstream projects has not been assessed.

The DOGV date endpoint handled the 30-day window cleanly. Special or supplemental issue behavior
should still be reviewed before larger historical backfills.

BOCM remains paused separately because of external endpoint/connectivity instability during its
metadata backfill.

## Next Recommended Task

Recommended next task:

```text
TASK-AUTO-DOGV-004 — DOGV candidate dry-run
```

Scope should remain dry-run only:

```text
no candidate writes
no PDF downloads
no downstream writes
no approvals
no publications
```

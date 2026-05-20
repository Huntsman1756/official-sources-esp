# BOE 6-Month Summary Backfill - 2026-05-20

## Scope

This report documents a controlled BOE summary-only backfill for `official-sources`.

Target range:

```text
2025-11-20 to 2026-05-20
```

This task did not download XML, HTML or PDF artifacts. It did not run candidate discovery. It did not create source candidates. It did not write to any downstream project.

## Deployment State

- Deployed commit: `160e3d6`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- Pre-run DB validation: valid

## Pre-Run Coverage

Selected status checks before the backfill:

| Date | Summary status | HTTP status | Documents | Artifact files |
|---|---|---:|---:|---:|
| `2025-11-20` | `none` | none | 0 | 0 |
| `2026-05-20` | `none` | none | 0 | 0 |

Pre-run database counts:

| Item | Count |
|---|---:|
| `official_documents` | 4,412 |
| `ingestion_runs` | 41 |
| `source_candidates` | 25 |
| `artifact_download_attempts` | 366 |
| `document_files` | 4,778 |

Pre-run artifact directory size:

```text
23M
```

## Pre-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_before_6m_summary_backfill_20260520_043627.sqlite
```

Result:

- Status: created successfully
- Size: 10M

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-boe-range \
  --date-from 2025-11-20 \
  --date-to 2026-05-20 \
  --skip-existing \
  --continue-on-no-publication \
  --stop-on-error \
  --max-days 190 \
  --sleep-seconds 1
```

No artifact download command was run.

No candidate discovery command was run.

## Backfill Result

The command exited non-zero because the final target date returned a BOE summary `404`.

Command output summary:

| Metric | Value |
|---|---:|
| Processed days | 150 |
| Skipped days | 32 |
| Success days | 128 |
| No-publication days | 21 |
| Failed days | 1 |
| Stopped on | `2026-05-20` |

Run rows created after the pre-run backup:

| Status | HTTP status | Days | Documents fetched | Documents new | Documents updated | Retries | Throttle events |
|---|---:|---:|---:|---:|---:|---:|---:|
| `success` | 200 | 128 | 17,215 | 17,215 | 0 | 0 | 36 |
| `no_publication` | 404 | 21 | 0 | 0 | 0 | 0 | 1 |
| `failed` | 404 | 1 | 0 | 0 | 0 | 0 | 0 |

Run totals:

| Metric | Value |
|---|---:|
| Documents fetched | 17,215 |
| Documents new | 17,215 |
| Documents updated | 0 |
| Retry count | 0 |
| Throttle events | 37 |

HTTP status summary:

```text
summary:200:128
summary:404:no_publication:21
summary:404:failed:1
```

The failed date was:

```text
2026-05-20
```

Status for `2026-05-20` after the run:

```text
summary_ingestion_status=failed
summary_last_http_status=404
documents=0
xml_files=0
html_files=0
pdf_files=0
```

## Post-Run Database State

Post-run DB validation:

```text
valid
```

Post-run database counts:

| Item | Count |
|---|---:|
| `official_documents` | 21,627 |
| `official_documents` in target range | 21,513 |
| `ingestion_runs` | 191 |
| `ingestion_runs` in target range | 185 |
| `source_candidates` | 25 |
| `artifact_download_attempts` | 366 |
| `document_files` | 21,993 |

`source_candidates` remained unchanged at 25.

`artifact_download_attempts` remained unchanged at 366.

## Artifact Size

| Moment | Size |
|---|---:|
| Before | 23M |
| After | 23M |

The artifact directory did not grow unexpectedly.

## Selected Status Outputs

### `2025-11-20`

```text
summary_ingestion_status=success
summary_last_http_status=200
documents=158
xml_files=0
html_files=0
pdf_files=0
artifact_http_status_summary=none
```

### `2026-01-01`

```text
summary_ingestion_status=success
summary_last_http_status=200
documents=52
xml_files=0
html_files=0
pdf_files=0
artifact_http_status_summary=none
```

### `2026-05-20`

```text
summary_ingestion_status=failed
summary_last_http_status=404
documents=0
xml_files=0
html_files=0
pdf_files=0
artifact_http_status_summary=none
```

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

Expected SSH and local resolver listeners were present.

## Post-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_after_6m_summary_backfill_20260520_044444.sqlite
```

Result:

- Status: created successfully after DB validation
- Size: 43M

## Known Issues

- The inclusive target end date `2026-05-20` returned BOE summary `404` and was recorded as `failed`.
- Because `--stop-on-error` was enabled, the command exited non-zero after that final failed date.
- This report treats the run as partially successful with one known failed date, not as a fully clean backfill.
- No manual retry was attempted.
- The task remains summary-only; XML/HTML/PDF evidence artifacts were not downloaded.
- No new BOE candidates were created.

## Next Recommended Task

Recommended next task:

```text
TASK-005B - BOE 6-month candidate dry-run
```

Before candidate creation, use a dry-run to measure the 6-month candidate volume against the now-expanded BOE summary metadata. If the volume is too high, refine the profile before creating candidates.

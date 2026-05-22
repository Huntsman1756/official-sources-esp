# DOGV Selected Candidate Evidence Download Retry - 2026-05-21

## Summary

TASK-AUTO-DOGV-007 was retried after TASK-AUTO-DOGV-007B added scoped DOGV PDF artifact download
support.

The retry downloaded official PDF evidence only for the 10 selected DOGV candidates. It did not
download by date range, did not create candidates, did not change candidate review status, did not
write downstream, and did not approve or publish anything.

## Deployed Code

```text
deployed_commit=e0784f7
command=download-source-artifacts
database=/opt/official-sources/data/official_sources.sqlite
artifact_dir=/opt/official-sources/data/artifacts
db_validation_before=current_version=8 latest_version=8 status=valid
```

## Scope

```text
source=DOGV
candidate_ids=101,102,103,104,106,108,109,111,117,124
candidate_count=10
types=pdf
expected_max_attempts=10
```

The command used persisted `url_pdf` values only.

## Pre-Run State

```text
source_candidates_total_before=125
DOGV_candidates_total_before=25
review_status_distribution_before=human_review_required:125
selected_review_status_distribution_before=human_review_required:10
artifact_download_attempts_before=432
document_files_total_before=26005
DOGV_pdf_document_files_before=0
selected_pdf_document_files_before=0
artifact_directory_size_before=26M
```

## Backup Before Download

Verified backup created with `db backup --full-check`:

```text
backup_before=/opt/official-sources/data/backups/official_sources_before_dogv_selected_evidence_retry_20260522_183122.sqlite
backup_before_size=53M
backup_before_status=verified
```

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source DOGV \
  --candidate-ids 101,102,103,104,106,108,109,111,117,124 \
  --types pdf
```

## Download Result

```text
selected_documents=10
artifact_types=pdf
downloaded=10
skipped=0
changed=0
failed=0
missing_artifact_url=0
retries=0
throttle_events=8
http_status_summary=pdf:200:10
```

The run stayed within the expected maximum of 10 attempts.

## Stored PDF Evidence

| candidate_id | official_identifier | size_bytes | sha256_prefix |
| ---: | --- | ---: | --- |
| 101 | `DOGV:DOGV-C-2026-16062` | 401393 | `f6cd369114b8` |
| 102 | `DOGV:DOGV-C-2026-16067` | 402739 | `1b2b694c4f9e` |
| 103 | `DOGV:DOGV-C-2026-16321` | 399925 | `20563ab838e4` |
| 104 | `DOGV:DOGV-C-2026-15641` | 406353 | `ecbf2f3ef5f3` |
| 106 | `DOGV:DOGV-C-2026-15801` | 400610 | `8338c645f59c` |
| 108 | `DOGV:DOGV-C-2026-15504` | 400327 | `d1b484c1ae57` |
| 109 | `DOGV:DOGV-C-2026-15505` | 398797 | `aca6af180953` |
| 111 | `DOGV:DOGV-C-2026-14623` | 405849 | `466142c7d681` |
| 117 | `DOGV:DOGV-C-2026-14923` | 403298 | `9b8b2d85c12e` |
| 124 | `DOGV:DOGV-C-2026-14022` | 400483 | `40c04381ea68` |

## Post-Run State

```text
source_candidates_total_after=125
DOGV_candidates_total_after=25
review_status_distribution_after=human_review_required:125
selected_review_status_distribution_after=human_review_required:10
artifact_download_attempts_after=442
document_files_total_after=26015
DOGV_pdf_document_files_after=10
selected_pdf_document_files_after=10
artifact_directory_size_after=30M
db_validation_after=current_version=8 latest_version=8 status=valid
```

Expected state changes:

```text
artifact_download_attempts: 432 -> 442
DOGV_pdf_document_files: 0 -> 10
selected_pdf_document_files: 0 -> 10
artifact_directory_size: 26M -> 30M
source_candidates_total: 125 -> 125
review_status_distribution: human_review_required:125 -> human_review_required:125
```

## Backup After Download

Verified backup created with `db backup --full-check`:

```text
backup_after=/opt/official-sources/data/backups/official_sources_after_dogv_selected_evidence_retry_20260522_183256.sqlite
backup_after_size=53M
backup_after_status=verified
```

## MCP Privacy

Command:

```bash
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener reported
```

## Safety Confirmation

```text
no date-range DOGV artifact download
no DOGV backfill
no new candidates
no source_candidate review_status changes
no downstream writes
no EduAyudas touch
no la-ayuda touch
no approvals
no publications
no MCP exposure
```

## Known Limitations

The PDFs are downloaded and recorded, but their contents have not been reviewed yet. This task only
established scoped evidence availability and local artifact integrity.

HTML/XML DOGV evidence remains unsupported by the downloader and should not be added until there is a
separate extraction and review design.

## Next Recommended Task

```text
TASK-AUTO-DOGV-008 - DOGV selected candidate evidence review
```

Recommended scope:

```text
candidate_ids=101,102,103,104,106,108,109,111,117,124
evidence_type=pdf
decision_labels=accept_for_downstream_pilot,needs_more_evidence,out_of_scope,false_positive,defer
no_downstream_writes=true
no_approval=true
no_publication=true
```

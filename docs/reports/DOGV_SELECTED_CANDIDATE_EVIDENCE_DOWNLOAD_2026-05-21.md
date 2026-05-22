# DOGV Selected Candidate Evidence Download - 2026-05-21

## Summary

TASK-AUTO-DOGV-007 inspected the selected DOGV candidates for scoped evidence download.

The selected candidates all have official DOGV PDF, HTML, XML, and metadata URLs persisted in the
database. The preferred evidence type is official PDF.

The download was not executed because the deployed and local CLI do not yet expose a supported DOGV
artifact download path. The available command is `download-boe-artifacts`, and its `--source` choices
are currently limited to `BOE` and `BOJA`. There is no `download-source-artifacts` command.

No manual download was attempted. No direct database writes were made. No candidates were created or
modified. No downstream project was touched. Nothing was approved or published. MCP exposure was
unchanged.

## Deployed State

```text
vps_checkout_commit=55170ee
local_main_before_report=d123b1383cdd5da8a951780b628dd448c053101b
database=/opt/official-sources/data/official_sources.sqlite
db_validation=current_version=8 latest_version=8 status=valid
```

The VPS checkout contains the DOGV candidate profile code used to create the candidates. Later local
commits were report-only and were not required for this read-only URL inspection.

## Selected Candidates

```text
selected_candidate_ids=101,102,103,104,106,108,109,111,117,124
selected_count=10
source_code=DOGV
review_status_expected=human_review_required
```

All selected candidates were present, belonged to `DOGV`, and remained in
`human_review_required`.

## URL Availability

| candidate_id | document_id | official_identifier | html_url | xml_url | pdf_url | metadata_url | integrity_warning |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 101 | 25526 | `DOGV:DOGV-C-2026-16062` | yes | yes | yes | yes | no |
| 102 | 25532 | `DOGV:DOGV-C-2026-16067` | yes | yes | yes | yes | no |
| 103 | 25524 | `DOGV:DOGV-C-2026-16321` | yes | yes | yes | yes | no |
| 104 | 25487 | `DOGV:DOGV-C-2026-15641` | yes | yes | yes | yes | no |
| 106 | 25482 | `DOGV:DOGV-C-2026-15801` | yes | yes | yes | yes | no |
| 108 | 25427 | `DOGV:DOGV-C-2026-15504` | yes | yes | yes | yes | no |
| 109 | 25424 | `DOGV:DOGV-C-2026-15505` | yes | yes | yes | yes | no |
| 111 | 25324 | `DOGV:DOGV-C-2026-14623` | yes | yes | yes | yes | no |
| 117 | 25330 | `DOGV:DOGV-C-2026-14923` | yes | yes | yes | yes | no |
| 124 | 25164 | `DOGV:DOGV-C-2026-14022` | yes | yes | yes | yes | no |

Summary:

```text
pdf_url_available=10
html_url_available=10
xml_url_available=10
metadata_url_available=10
missing_artifact_url_count=0
integrity_warning_count=0
```

## Evidence Type Decision

Preferred evidence type:

```text
official_pdf
```

Reason:

```text
All selected candidates have persisted official DOGV PDF URLs.
PDF is the clearest official artifact for scoped human evidence review.
```

However, no PDF download was performed because there is no supported DOGV downloader command yet.

## Command Capability Check

Available deployed command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  download-boe-artifacts --help
```

Observed support:

```text
command=download-boe-artifacts
supported_sources=BOE,BOJA
candidate_id_scope_supported=yes
pdf_type_supported=yes
DOGV_source_supported=no
download-source-artifacts_exists=no
```

Because DOGV is not accepted by the supported downloader, this task stopped before backup/download.
No unsupported manual write path was used.

## Download Result

```text
download_executed=false
blocker=unsupported_dogv_artifact_downloader
downloaded=0
skipped=10
failed=0
changed=0
missing_artifact_url=0
http_status_summary=not_applicable
retry_count=0
throttle_events=0
```

## Backup Result

```text
backup_before_download=not_created
backup_after_download=not_created
reason=no_download_or_database_write_was_attempted
```

The plan required a backup before download. Since the task stopped before any write/download step,
creating operational backups was unnecessary.

## State Verification

Pre/post state remained unchanged:

```text
source_candidates_total=125 -> 125
DOGV_candidates_total=25 -> 25
review_status_distribution=human_review_required:125 -> human_review_required:125
selected_review_status_distribution=human_review_required:10 -> human_review_required:10
artifact_download_attempts=432 -> 432
document_files_total=26005 -> 26005
DOGV_pdf_document_files=0 -> 0
selected_pdf_document_files=0 -> 0
artifact_directory_size=26M -> 26M
db_validation=current_version=8 latest_version=8 status=valid
```

No downstream writes, approvals, publications, DOGV backfills, or new candidates were performed.

## MCP Privacy

Command:

```bash
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener reported
```

## Known Limitations

The data is ready for scoped DOGV PDF evidence download, but the platform command surface is not.
The existing downloader is still named and constrained around BOE/BOJA:

```text
download-boe-artifacts --source BOE|BOJA
```

The next implementation should add DOGV support to a generic source artifact downloader or extend the
existing downloader safely, preserving scoped candidate/document ID limits.

## Recommended Next Task

```text
TASK-AUTO-DOGV-007B - Enable scoped DOGV artifact downloader
```

Recommended scope:

```text
add DOGV support to scoped artifact download command
support --candidate-ids and --document-ids only for DOGV
support --types pdf initially
hard-limit candidate count to 10 for first DOGV run
reuse persisted url_pdf only
do not infer or construct URLs
add tests for source=DOGV, types=pdf, candidate scope, and no range download
```

After that, rerun TASK-AUTO-DOGV-007 with:

```text
candidate_ids=101,102,103,104,106,108,109,111,117,124
types=pdf
expected_attempts=10
```

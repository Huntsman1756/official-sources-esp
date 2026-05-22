# DOGV Downstream Evidence Export - 2026-05-21

## Summary

TASK-AUTO-DOGV-010 exported accepted DOGV evidence into downstream-ready JSON files on the VPS.

This task did not write to EduAyudas or `la-ayuda`. It did not create downstream candidates, drafts,
approvals, publications, additional artifact downloads, DOGV backfills, or MCP exposure.

## VPS State

```text
vps_checkout_commit=e0784f7
local_main_before_report=039e7c3745630c99e7f0ceed7a381c2f62f7af3a
database=/opt/official-sources/data/official_sources.sqlite
db_validation=current_version=8 latest_version=8 status=valid
```

Input decisions:

```text
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
source_candidates.review_status=human_review_required
```

## Exported Candidates

```text
exported_total=10
EduAyudas=101,102,103,104,106,108,109,111,124
la-ayuda=117
```

## Export Directories

Files were created outside Git:

```text
/opt/official-sources/data/downstream_exports/2026-05-21/dogv/eduayudas/
/opt/official-sources/data/downstream_exports/2026-05-21/dogv/la-ayuda/
```

File counts:

```text
eduayudas_json_files=9
la_ayuda_json_files=1
total_json_files=10
```

Example filenames:

```text
eduayudas/101_DOGV_DOGV-C-2026-16062.json
eduayudas/111_DOGV_DOGV-C-2026-14623.json
la-ayuda/117_DOGV_DOGV-C-2026-14923.json
```

## Export Schema

Each JSON includes:

```text
source_code
resource_type
official_identifier
title
publication_date
official_url
citation
integrity
artifacts
official_sources_candidate
dogv_metadata
safety
```

The export uses official DOGV URLs and artifact hashes, but excludes:

```text
raw PDF text
raw XML/HTML
local artifact paths
VPS public IP
secrets
```

## JSON Validation

Validation result:

```text
files_parsed=10
required_fields_present=10/10
eduayudas_count=9
la_ayuda_count=1
source_code_DOGV=10/10
manual_decision_accept_for_downstream_pilot=10/10
review_status_human_review_required=10/10
pdf_available=10/10
selected_for_pdf_false=10/10
forbidden_token_errors=0
```

Forbidden-token scan covered:

```text
/opt/official-sources
VPS public IP
.env
.venv
PRIVATE KEY
BEGIN RSA
raw_pdf_text
raw_xml
raw_html
```

## DB And Artifact Safety

Pre/post verification remained unchanged:

```text
source_candidates=125 -> 125
candidate_evidence_reviews=45 -> 45
artifact_download_attempts=442 -> 442
document_files=26015 -> 26015
source_candidates.review_status_distribution=human_review_required:125
artifact_directory_size=30M -> 30M
db_validation=current_version=8 latest_version=8 status=valid
```

No DB writes were performed by the export.

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

The JSON files are staging exports only. They are not imported into downstream projects and should not
be treated as published aid pages or approved downstream records.

The export preserves official evidence metadata and hashes, but does not include raw PDF text or full
eligibility extraction. A downstream import task should still validate field mapping in the target
project before creating any records.

## Recommended Next Task

```text
TASK-AUTO-DOGV-011 - Review DOGV downstream export schema
```

Recommended scope:

```text
read exported JSON only
confirm target field mapping for EduAyudas and la-ayuda
do not write downstream
do not publish
```

After downstream fixes are closed and mappings are approved, a later task can import the staged JSON
into each destination separately.

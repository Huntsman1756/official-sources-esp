# DOGV Downstream Export Schema Review - 2026-05-21

## Summary

TASK-AUTO-DOGV-011 reviewed the DOGV downstream export JSON files created by
TASK-AUTO-DOGV-010.

This was review-only. No import into EduAyudas or `la-ayuda` was performed. No downstream candidates,
drafts, approvals, publications, artifact downloads, DB mutations, or MCP exposure were created.

## VPS State

```text
vps_checkout_commit=e0784f7
local_main_before_report=f7938c241fcf8e168c764a3a87c9dbb31f57a538
database=/opt/official-sources/data/official_sources.sqlite
db_validation=current_version=8 latest_version=8 status=valid
```

Exports reviewed:

```text
/opt/official-sources/data/downstream_exports/2026-05-21/dogv/eduayudas/
/opt/official-sources/data/downstream_exports/2026-05-21/dogv/la-ayuda/
```

## Files Reviewed

```text
total_json_files=10
eduayudas_json_files=9
la_ayuda_json_files=1
```

EduAyudas files:

```text
101_DOGV_DOGV-C-2026-16062.json
102_DOGV_DOGV-C-2026-16067.json
103_DOGV_DOGV-C-2026-16321.json
104_DOGV_DOGV-C-2026-15641.json
106_DOGV_DOGV-C-2026-15801.json
108_DOGV_DOGV-C-2026-15504.json
109_DOGV_DOGV-C-2026-15505.json
111_DOGV_DOGV-C-2026-14623.json
124_DOGV_DOGV-C-2026-14022.json
```

la-ayuda file:

```text
117_DOGV_DOGV-C-2026-14923.json
```

## Schema Validation Result

Required root fields were present in all 10 files:

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
```

Integrity fields were present in all 10 files:

```text
source_snapshot_hash
content_sha256
hashes_match
has_integrity_warning
integrity_warning_reason
```

Artifact checks:

```text
pdf_available=true: 10/10
xml_available=false: 10/10
html_available=false: 10/10
pdf official URL present: 10/10
pdf size_bytes present: 10/10
pdf sha256 present: 10/10
```

Safety checks:

```text
local filesystem paths: none
raw PDF text: none
raw XML/HTML: none
secrets: none
VPS public IP: none
```

Decision checks:

```text
manual_decision=accept_for_downstream_pilot: 10/10
evidence_review_status=evidence_reviewed: 10/10
review_status=human_review_required: 10/10
```

Routing checks:

```text
EduAyudas downstream_project_fit: 9/9
la-ayuda downstream_project_fit: 1/1
```

## EduAyudas Compatibility

Compatibility status:

```text
usable_for_preview_import_after_mapping_review
```

The EduAyudas files contain the minimum evidence metadata needed for a preview importer:

```text
source identifier and title
publication date
official DOGV URL
PDF evidence URL and SHA-256
candidate decision metadata
DOGV metadata keys
routing marker downstream_project_fit=EduAyudas
```

Known schema gaps for EduAyudas before real import:

```text
No normalized education stage field.
No normalized beneficiary age/student segment.
No normalized amount/budget fields.
No normalized deadline date.
No extracted application channel URL beyond cited official sources.
No extracted documentation requirements.
```

These gaps do not block a single preview import if the downstream importer treats the JSON as
evidence metadata and keeps the item in draft/review. They do block automatic publication or broad
bulk import.

## la-ayuda Compatibility

Compatibility status:

```text
usable_for_single_preview_import_after_mapping_review
```

The la-ayuda file for candidate `117` contains the minimum metadata needed for a preview:

```text
source identifier and title
publication date
official DOGV URL
PDF evidence URL and SHA-256
candidate decision metadata
routing marker downstream_project_fit=la-ayuda
```

Known schema gaps for la-ayuda before real import:

```text
No normalized target population taxonomy.
No normalized amount/payment fields.
No normalized deadline date.
No extracted eligibility conditions.
No extracted application channel.
No extracted governing order details.
```

Candidate `117` is likely compatible with a metadata-only preview because it is direct worker support,
but it should not be published without a downstream review step.

## Cross-Destination Gaps

The export schema is safe but intentionally evidence-centric. It does not yet provide fully normalized
downstream product fields.

Important gaps:

```text
No canonical downstream slug/title normalization.
No normalized monetary amount object.
No normalized deadline object.
No extracted eligibility/documentation/application steps.
No downstream category mapping beyond downstream_project_fit.
No language/locale field for Valencian/Spanish variants.
No import idempotency key beyond candidate_id and official_identifier.
```

Recommended importer behavior:

```text
derive idempotency from source_code + official_identifier + candidate_id
store official evidence metadata exactly
keep imported records in preview/draft state
require human review before any public page or downstream approval
```

## Risks

```text
Importing all 9 EduAyudas records at once could expose importer mapping issues across repeated university scholarship shapes.
The JSON contains evidence metadata, not full extracted aid content.
DOGV extract PDFs often point to university/BOUA bases for complete requirements.
The current schema is suitable for staging, not final publication.
```

## Recommendation

Recommendation:

```text
do_not_bulk_import_yet
```

Recommended next action:

```text
import exactly one DOGV export into a downstream preview/draft path
```

Preferred first test:

```text
TASK-AUTO-DOGV-012 - Import 1 DOGV evidence into la-ayuda preview
candidate_id=117
```

Alternative after EduAyudas is stable:

```text
TASK-DOGV-EDUAYUDAS-RUN1 - Preview 1 DOGV evidence file in EduAyudas
candidate_id=101 or 111
```

## Safety Verification

DB validation:

```text
current_version=8 latest_version=8 status=valid
```

MCP privacy:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
result=no matching listener reported
```

No DB mutation or downstream write was performed during this review.

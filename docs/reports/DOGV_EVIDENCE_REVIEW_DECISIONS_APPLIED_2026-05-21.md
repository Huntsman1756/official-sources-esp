# DOGV Evidence Review Decisions Applied - 2026-05-21

## Summary

TASK-AUTO-DOGV-009 applied DOGV evidence review decisions to `candidate_evidence_reviews`.

This was operational evidence metadata only. No downstream project was touched. No candidates were
created. `source_candidates.review_status` was not changed. Nothing was approved or published. No
artifacts were downloaded. No DOGV backfill was run. MCP exposure was unchanged.

## Deployed State

```text
vps_checkout_commit=e0784f7
database=/opt/official-sources/data/official_sources.sqlite
db_validation_before=current_version=8 latest_version=8 status=valid
```

Latest evidence review report:

```text
docs/reports/DOGV_SELECTED_CANDIDATE_EVIDENCE_REVIEW_2026-05-21.md
```

## Candidates Updated

```text
candidate_ids=101,102,103,104,106,108,109,111,117,124
updated_count=10
source_code=DOGV for all 10
pdf_available=true for all 10
integrity_warning=false for all 10
review_status_before=human_review_required for all 10
review_status_after=human_review_required for all 10
```

Before this task, none of the 10 selected DOGV candidates had a `candidate_evidence_reviews` row.

## Backup Before Write

Verified backup created with `db backup --full-check`:

```text
backup_before=/opt/official-sources/data/backups/official_sources_before_dogv_review_apply_20260522_192954.sqlite
backup_before_size=53M
backup_before_status=verified
```

## Decisions Applied

Common fields:

```text
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
reviewed_by=Dani
reviewed_at=2026-05-21
selected_for_pdf=false
needs_pdf=no
```

Routing:

| downstream_project_fit | candidates | count |
| --- | --- | ---: |
| `EduAyudas` | `101,102,103,104,106,108,109,111,124` | 9 |
| `la-ayuda` | `117` | 1 |

Decision distribution:

| manual_decision | count |
| --- | ---: |
| `accept_for_downstream_pilot` | 10 |

Evidence status distribution:

| evidence_review_status | evidence_label | selected_for_pdf | pdf_available | count |
| --- | --- | ---: | ---: | ---: |
| `evidence_reviewed` | `likely_relevant` | 0 | 1 | 10 |

## Verification Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  candidate-evidence-status \
  --candidate-ids 101,102,103,104,106,108,109,111,117,124
```

Verified state:

```text
accept_for_downstream_pilot=10
selected_for_pdf=0
pdf_available=10
reviewed_by=Dani
reviewed_at=2026-05-21
```

## Safety Verification

```text
source_candidates_total=125
source_candidates.review_status_distribution=human_review_required:125
candidate_evidence_reviews=35 -> 45
artifact_download_attempts=442 -> 442
document_files=26015 -> 26015
artifact_directory_size=30M -> 30M
db_validation_after=current_version=8 latest_version=8 status=valid
```

No downstream writes, approvals, publications, DOGV backfills, artifact downloads, or new candidates
were performed.

## Backup After Write

Verified backup created with `db backup --full-check`:

```text
backup_after=/opt/official-sources/data/backups/official_sources_after_dogv_review_apply_20260522_193056.sqlite
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

## Known Limitations

These decisions are operational evidence metadata. They do not create downstream exports and do not
approve or publish any item.

`source_candidates.review_status` intentionally remains `human_review_required` for all candidates.

## Recommended Next Task

```text
TASK-AUTO-DOGV-010 - Export DOGV accepted evidence for downstream staging
```

Recommended scope:

```text
export JSON only
EduAyudas candidates=101,102,103,104,106,108,109,111,124
la-ayuda candidates=117
no writes to downstream repositories
no approvals
no publications
```

# BOJA Evidence Review Decisions Applied - 2026-05-20

## Scope

This report documents applying BOJA selected candidate evidence review decisions to
`candidate_evidence_reviews`.

Updated candidate IDs:

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

This task updated only operational evidence review metadata.

This task did not change `source_candidates.review_status`, did not approve candidates, did not
publish anything, did not download more artifacts, and did not write to downstream projects.

## Deployment State

```text
deployed_commit=6466f23
schema_version=8
journal_mode=wal
synchronous=normal
pre_run_db_validation=valid
```

The VPS code was sufficient for evidence decision application and database validation.

## Pre-Run Verification

The selected candidates existed and had BOJA PDF evidence available:

```text
selected_count=10
source_code=BOJA for all selected candidates
review_status=human_review_required for all selected candidates
pdf_available=10/10
pdf_hash_present=10/10
integrity_warning=0
existing_candidate_evidence_reviews_for_selected=0
```

Pre-run counts:

| Item | Count |
| --- | ---: |
| `source_candidates` | 100 |
| `source_candidates.human_review_required` | 100 |
| `artifact_download_attempts` | 432 |
| BOJA PDF `document_files` | 10 |
| Artifact directory size | 26M |

## Pre-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_before_boja_evidence_review_apply_20260520_164233.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49049600
status=success
```

## Decisions Applied

### Accepted For Downstream Pilot

```text
77, 78, 80, 86
```

Applied fields:

```text
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
downstream_project_fit=EduAyudas
needs_pdf=no
selected_for_pdf=false
reviewed_by=Dani
reviewed_at=2026-05-20
```

Routing:

| Candidate ID | Downstream fit |
| ---: | --- |
| 77 | `EduAyudas` |
| 78 | `EduAyudas` |
| 80 | `EduAyudas` |
| 86 | `EduAyudas` |

### Out Of Scope

```text
79, 81, 82, 87, 93, 98
```

Applied fields:

```text
manual_decision=out_of_scope
evidence_label=out_of_scope
evidence_review_status=out_of_scope
downstream_project_fit=neither
needs_pdf=no
selected_for_pdf=false
reviewed_by=Dani
reviewed_at=2026-05-20
```

The out-of-scope group contains real official documents, but they are not suitable for current
downstream pilot fichas. Several are award resolutions, notifications, or proceeding-specific
notices rather than reusable open calls.

Candidate `81` remains out of scope for `la-ayuda`: it mentions housing/youth aid, but the evidence
is a notification for existing proceedings, not a general open aid call.

## Decision Distribution

| Field | Value | Count |
| --- | --- | ---: |
| `manual_decision` | `accept_for_downstream_pilot` | 4 |
| `manual_decision` | `out_of_scope` | 6 |
| `evidence_review_status` | `evidence_reviewed` | 4 |
| `evidence_review_status` | `out_of_scope` | 6 |
| `needs_pdf` | `no` | 10 |
| `selected_for_pdf` | `false` | 10 |

PDF evidence summary:

```text
pdf_available=10/10
needs_pdf=yes=0
selected_for_pdf=true=0
```

## Post-Run Verification

`source_candidates.review_status` remained unchanged:

| Review status | Count |
| --- | ---: |
| `human_review_required` | 100 |

Artifact counts remained unchanged during this task:

| Item | Before | After |
| --- | ---: | ---: |
| Artifact directory size | 26M | 26M |
| `artifact_download_attempts` | 432 | 432 |
| BOJA PDF `document_files` | 10 | 10 |

DB validation:

```text
valid
```

## MCP Privacy

Listener checks for `official`, `mcp`, `python`, `uvicorn`, and `fastmcp` returned no matching
listeners.

No public MCP listener or SQLite exposure was observed.

## Post-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_after_boja_evidence_review_apply_20260520_164339.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49049600
status=success
```

## Known Limitations

- This is an operational evidence review update, not legal advice.
- No downstream import was performed.
- No approval or publication occurred.
- BOJA HTML/XML evidence remains unavailable in the current path.
- The accepted BOJA candidates are only routed as downstream pilot candidates; they have not been
  exported or imported into EduAyudas.
- Historical `ingestion_runs` and `artifact_download_attempts` still include earlier failed or
  skipped operational attempts. Current status should use the latest evidence review rows and
  current `document_files`.

## Next Recommended Task

Recommended next task:

```text
TASK-AUTO-010 - BOJA pilot closure and downstream strategy decision
```

Scope:

- summarize the BOJA pilot results end to end;
- decide whether to export `77, 78, 80, 86` for EduAyudas staging;
- keep downstream import, approval, and publication out of the closure task unless explicitly
  approved later.

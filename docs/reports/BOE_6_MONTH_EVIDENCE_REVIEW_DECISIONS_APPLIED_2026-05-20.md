# BOE 6-Month Evidence Review Decisions Applied - 2026-05-20

## Scope

This report documents applying the selected 6-month BOE evidence review decisions to `candidate_evidence_reviews`.

Updated candidate IDs:

```text
32, 36, 40, 42, 44, 49, 56, 57, 58, 60, 68, 69, 72
```

This task updated only operational evidence review metadata.

This task did not change `source_candidates.review_status`, did not approve candidates, did not publish anything, did not download more artifacts, and did not write to downstream projects.

## Deployment State

- Deployed commit: `98c6fe8`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- Pre-run DB validation: valid

## Pre-Run Verification

All 13 selected candidates existed and had:

```text
review_status=human_review_required
xml_available=true
html_available=true
pdf_available=false
integrity_warning=false
```

Pre-run counts:

| Item | Count |
|---|---:|
| `source_candidates` | 75 |
| `source_candidates.human_review_required` | 75 |
| `artifact_download_attempts` | 392 |
| `document_files.xml` | 137 |
| `document_files.html` | 137 |
| `document_files.pdf` | 118 |
| Artifact directory size | 24M |

## Pre-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_before_6m_evidence_review_apply_20260520_074757.sqlite
```

Result:

- Status: created successfully
- Size: 44M

## Decisions Applied

### Accepted For Downstream Pilot

```text
36, 40, 49, 60, 69
```

Applied fields:

```text
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
needs_pdf=no
selected_for_pdf=false
reviewed_by=Dani
reviewed_at=2026-05-20
```

Routing:

| Candidate ID | Downstream fit |
|---:|---|
| 36 | `EduAyudas` |
| 40 | `EduAyudas` |
| 49 | `EduAyudas` |
| 60 | `EduAyudas` |
| 69 | `la-ayuda` |

### Deferred

```text
42, 44, 57, 58
```

Applied fields:

```text
manual_decision=defer
evidence_label=unclear
evidence_review_status=evidence_reviewed
downstream_project_fit=unclear
needs_pdf=no
selected_for_pdf=false
reviewed_by=Dani
reviewed_at=2026-05-20
```

### Out Of Scope

```text
32, 56, 68, 72
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

## Decision Distribution

| Field | Value | Count |
|---|---|---:|
| `manual_decision` | `accept_for_downstream_pilot` | 5 |
| `manual_decision` | `defer` | 4 |
| `manual_decision` | `out_of_scope` | 4 |
| `evidence_review_status` | `evidence_reviewed` | 9 |
| `evidence_review_status` | `out_of_scope` | 4 |
| `needs_pdf` | `no` | 13 |
| `selected_for_pdf` | `false` | 13 |

PDF selection status:

```text
needs_pdf=yes: 0
selected_for_pdf=true: 0
```

No PDF was downloaded.

## Post-Run Verification

`source_candidates.review_status` remained unchanged:

| Review status | Count |
|---|---:|
| `human_review_required` | 75 |

Artifact counts remained unchanged:

| Item | Before | After |
|---|---:|---:|
| Artifact directory size | 24M | 24M |
| `artifact_download_attempts` | 392 | 392 |
| `document_files.xml` | 137 | 137 |
| `document_files.html` | 137 | 137 |
| `document_files.pdf` | 118 | 118 |

DB validation:

```text
valid
```

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Post-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_after_6m_evidence_review_apply_20260520_074937.sqlite
```

Result:

- Status: created successfully after DB validation
- Size: 44M

## Known Limitations

- This is an operational evidence review update, not legal advice.
- No downstream import was performed.
- No approval or publication occurred.
- Candidate `69` is routed to `la-ayuda`, not EduAyudas.
- Deferred candidates may be useful later if downstream scope expands to narrow professional training grants.

## Next Recommended Task

Recommended next task:

```text
TASK-005H - Export accepted 6-month evidence for downstream staging
```

Suggested routing:

```text
EduAyudas: 36, 40, 49, 60
la-ayuda: 69
```

Do not publish or approve anything downstream. Import only into staging/review surfaces if the downstream project is ready.

# BOJA Selected Candidate Evidence Review - 2026-05-20

## Summary

TASK-AUTO-008 reviewed the 10 downloaded BOJA PDF evidence files selected from the first BOJA
candidate batch.

This was a review-only task. No downstream project was touched. No candidates were approved or
published. `source_candidates.review_status` remained unchanged.

## Deployed State

```text
deployed_commit=6466f23
schema_version=8
journal_mode=wal
synchronous=normal
DB validation=valid
```

Local report repository commit at the start of the review:

```text
31e90bc
```

The VPS code was sufficient for evidence inspection and database validation.

## Candidates Reviewed

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

Evidence availability:

```text
selected_count=10
source_code=BOJA for all selected candidates
review_status=human_review_required for all selected candidates
url_pdf present=10/10
pdf_available=10/10
pdf_hash_present=10/10
integrity_warning=0
```

## Review Table

| Candidate | Official identifier | Evidence finding | Decision | Downstream fit | Reason |
| --- | --- | --- | --- | --- | --- |
| 77 | `BOJA:disposition.2026.95.6` | University of Huelva master scholarship call for international students; amount, beneficiary requirements, and deadline are present. | `accept_for_downstream_pilot` | `EduAyudas` | Direct student scholarship with clear education scope and actionable call metadata. |
| 78 | `BOJA:disposition.2026.94.5` | University of Huelva Campus Rural practice aid call for students; budget, beneficiary requirements, registration context, and deadline are present. | `accept_for_downstream_pilot` | `EduAyudas` | Direct student/training aid with clear application window and education fit. |
| 79 | `BOJA:disposition.2026.93.28` | Resolution awarding six library training scholarships and listing selected/excluded applicants. | `out_of_scope` | `neither` | Real scholarship document, but it is an award/resolution after the call, not a reusable downstream aid listing. |
| 80 | `BOJA:disposition.2026.92.1` | Andalusian FP and arts/design student stays in other EU countries; call scope, student target, requirements framework, and procedure references are present. | `accept_for_downstream_pilot` | `EduAyudas` | Education/training mobility opportunity for students; enough evidence for a pilot candidate even though amount is not explicit in the PDF excerpt. |
| 81 | `BOJA:disposition.2026.92.55` | Housing aid notification notice for vulnerability/youth rental aid proceedings. | `out_of_scope` | `neither` | Broad citizen benefit topic, but this document is a notification of requirements/proposals/resolutions for existing proceedings, not an open aid call. |
| 82 | `BOJA:disposition.2026.91.73` | Employment training aid notification notice where a resolution could not be notified. | `out_of_scope` | `neither` | Real FPE aid context, but the document is an individual notification notice, not a downstream-ready aid program. |
| 86 | `BOJA:disposition.2026.90.5` | UPO Santander economic scholarship call for 100 students; amount, budget, requirements, application channel, deadline, payment and obligations are present. | `accept_for_downstream_pilot` | `EduAyudas` | Strong direct student aid with complete operational metadata. |
| 87 | `BOJA:disposition.2026.89.44` | Resolution awarding one training scholarship in the Faculty of Social Sciences and listing excluded applicants. | `out_of_scope` | `neither` | Real scholarship evidence, but closed award/resolution rather than an active aid call. |
| 93 | `BOJA:disposition.2026.86.57` | Resolution awarding one training scholarship linked to the Equality Office and listing excluded applicants. | `out_of_scope` | `neither` | Real scholarship evidence, but closed award/resolution rather than an active aid call. |
| 98 | `BOJA:disposition.2026.81.46` | Resolution awarding two Santander-linked sports talent training scholarships and listing excluded applicants. | `out_of_scope` | `neither` | Real scholarship evidence, but closed award/resolution rather than an active aid call. |

## Decision Distribution

```text
accept_for_downstream_pilot=4
needs_more_evidence=0
out_of_scope=6
false_positive=0
defer=0
```

Accepted for downstream pilot:

```text
77 -> EduAyudas
78 -> EduAyudas
80 -> EduAyudas
86 -> EduAyudas
```

Needs more evidence:

```text
none
```

Out of scope:

```text
79, 81, 82, 87, 93, 98
```

False positives:

```text
none
```

Deferred:

```text
none
```

## Routing Suggestions

Suggested routing:

```text
EduAyudas: 77, 78, 80, 86
la-ayuda: none
neither: 79, 81, 82, 87, 93, 98
```

Candidate 81 mentions housing/youth aid, but it should not be routed to `la-ayuda` yet because the
document is a notice for existing proceedings, not a general aid call.

## Verification

Post-review DB checks:

```text
source_candidates=100
artifact_download_attempts=432
BOJA PDF document_files=10
selected_pdf_files=10
selected_review_status_distribution=human_review_required:10
all_review_status_distribution=human_review_required:100
selected_integrity_warnings=0
artifact_directory_size=26M
DB validation=valid
```

MCP privacy:

```text
no matching listener observed
```

No public MCP listener or SQLite exposure was observed.

## Known Limitations

- The review is operational triage, not legal advice.
- BOJA HTML/XML evidence is still unavailable; this review used downloaded PDFs plus stored metadata.
- Accepted candidates are not yet written to downstream projects.
- Review decisions are report-only in this task; they have not yet been applied to
  `candidate_evidence_reviews`.
- Historical artifact attempt counts include earlier skipped/HTTP 307 attempts from URL enrichment
  and canonicalization work.

## Recommendation

Recommended next task:

```text
TASK-AUTO-009 - Apply BOJA evidence review decisions
```

Scope:

- write only operational decisions to `candidate_evidence_reviews`;
- keep `source_candidates.review_status=human_review_required`;
- do not write EduAyudas or la-ayuda;
- do not approve or publish.

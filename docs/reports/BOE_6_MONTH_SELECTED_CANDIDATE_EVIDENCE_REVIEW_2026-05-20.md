# BOE 6-Month Selected Candidate Evidence Review - 2026-05-20

## Scope

This report documents XML/HTML evidence review for the 13 selected BOE candidates from the 6-month batch.

Reviewed candidate IDs:

```text
32, 36, 40, 42, 44, 49, 56, 57, 58, 60, 68, 69, 72
```

This task reviewed existing XML/HTML evidence only.

This task did not download PDFs, did not download more XML/HTML, did not call BOE, did not run a backfill, did not create candidates, did not approve candidates, did not publish anything, and did not write to downstream projects.

Operational decisions in this report were not written to the database.

## Deployment State

- Deployed commit: `a76debb`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- DB validation: valid

## Evidence Availability

All reviewed candidates had XML and HTML evidence available before review.

| Candidate ID | Official identifier | XML | HTML | PDF | Integrity warning | Review status |
|---:|---|---:|---:|---:|---|---|
| 32 | `BOE-B-2026-16238` | yes | yes | no | no | `human_review_required` |
| 36 | `BOE-B-2026-14182` | yes | yes | no | no | `human_review_required` |
| 40 | `BOE-B-2026-14244` | yes | yes | no | no | `human_review_required` |
| 42 | `BOE-B-2026-13661` | yes | yes | no | no | `human_review_required` |
| 44 | `BOE-B-2026-13592` | yes | yes | no | no | `human_review_required` |
| 49 | `BOE-B-2026-13482` | yes | yes | no | no | `human_review_required` |
| 56 | `BOE-B-2026-13408` | yes | yes | no | no | `human_review_required` |
| 57 | `BOE-B-2026-12992` | yes | yes | no | no | `human_review_required` |
| 58 | `BOE-B-2026-12993` | yes | yes | no | no | `human_review_required` |
| 60 | `BOE-B-2026-13097` | yes | yes | no | no | `human_review_required` |
| 68 | `BOE-B-2026-12557` | yes | yes | no | no | `human_review_required` |
| 69 | `BOE-B-2026-12558` | yes | yes | no | no | `human_review_required` |
| 72 | `BOE-B-2026-12566` | yes | yes | no | no | `human_review_required` |

## Review Table

| Candidate | Official identifier | Beneficiary type | Direct citizen aid | Student/training aid | Entity/project subsidy | Evidence summary | Downstream fit | Decision | Needs PDF |
|---:|---|---|---|---|---|---|---|---|---|
| 32 | `BOE-B-2026-16238` | Non-profit legal entities | no | partly | yes | Subsidies for entity projects supporting women and girls victims of trafficking/exploitation and their children; budget and deadline present. | `neither` | `out_of_scope` | no |
| 36 | `BOE-B-2026-14182` | Natural persons and research teams | yes | yes | partly | CIS training/research grants, including individual data-bank research grants and doctoral thesis completion grants; requirements, amount, deadline and electronic channel present. | `EduAyudas` | `accept_for_downstream_pilot` | no |
| 40 | `BOE-B-2026-14244` | Natural persons | yes | yes | no | Six training scholarships in the Observatory on Violence against Women for recent graduates/certificate holders; amount, unemployment requirement, deadline and channel present. | `EduAyudas` | `accept_for_downstream_pilot` | no |
| 42 | `BOE-B-2026-13661` | Army military personnel | yes, restricted | yes | no | Aid for Master's in Military Law for active Army personnel; requirements, amount and deadline present. | `EduAyudas` | `defer` | no |
| 44 | `BOE-B-2026-13592` | Army officers/common corps | yes, restricted | yes | no | Aid for Master's in Occupational Risk Prevention for Army-related personnel; requirements, amount and deadline present. | `EduAyudas` | `defer` | no |
| 49 | `BOE-B-2026-13482` | Athletes | yes | yes | no | Scholarships for athletes at the Madrid high-performance center; beneficiary, purpose and funding present. | `EduAyudas` | `accept_for_downstream_pilot` | no |
| 56 | `BOE-B-2026-13408` | Non-profit entities | no | yes, indirect | yes | Cine Escuela support for audiovisual education activities in schools, but beneficiaries are non-profit entities. | `unclear` | `out_of_scope` | no |
| 57 | `BOE-B-2026-12992` | Army officers/sub-officers | yes, restricted | yes | no | Scholarship for Master's in Process Management for Army personnel; requirements, amount and deadline present. | `EduAyudas` | `defer` | no |
| 58 | `BOE-B-2026-12993` | Army officers/sub-officers | yes, restricted | yes | no | Scholarship for Master's in Big Data Analysis and Visualization for Army personnel; requirements, amount and deadline present. | `EduAyudas` | `defer` | no |
| 60 | `BOE-B-2026-13097` | Student theater groups | yes, group-based | yes | no | Education ministry aid for Spanish school theater festival participation by student groups in bilingual sections abroad; amount and deadline present. | `EduAyudas` | `accept_for_downstream_pilot` | no |
| 68 | `BOE-B-2026-12557` | Assistance institutions | no | no | yes | Subsidies to institutions assisting Spaniards abroad in need; useful social topic but entity-mediated and not direct aid. | `la-ayuda` | `out_of_scope` | no |
| 69 | `BOE-B-2026-12558` | Natural persons and non-profit entities | yes | no | partly | Legal-assistance aid for Spanish citizens facing death-penalty proceedings abroad; direct citizen beneficiary is explicit, amount and deadline present. | `la-ayuda` | `accept_for_downstream_pilot` | no |
| 72 | `BOE-B-2026-12566` | Unions, business organizations and related entities | no | yes, indirect | yes | State-level training plan subsidies for collective bargaining/social dialogue organizations; entity-targeted, not direct citizen/student aid. | `neither` | `out_of_scope` | no |

## Decision Distribution

| Decision | Count |
|---|---:|
| `accept_for_downstream_pilot` | 5 |
| `defer` | 4 |
| `out_of_scope` | 4 |
| `needs_more_evidence` | 0 |
| `false_positive` | 0 |

## Accepted For Downstream Pilot

Recommended for downstream pilot:

```text
36, 40, 49, 60, 69
```

Suggested downstream routing:

| Candidate ID | Fit | Reason |
|---:|---|---|
| 36 | `EduAyudas` | Training/research and doctoral aid with clear beneficiaries and amounts. |
| 40 | `EduAyudas` | Training scholarships for natural persons with clear eligibility and amount. |
| 49 | `EduAyudas` | Athlete scholarships; education/training support with clear beneficiary group. |
| 60 | `EduAyudas` | Student-group education aid tied to school theater participation. |
| 69 | `la-ayuda` | Citizen legal-assistance aid, not education-specific. |

## Deferred

Deferred:

```text
42, 44, 57, 58
```

Reason:

- These are real direct training aids with enough XML/HTML evidence.
- They are restricted to Army or Army-related personnel.
- They are too narrow for the immediate downstream pilot, but may be useful if EduAyudas later includes sector-specific professional training grants.

## Out Of Scope

Out of scope:

```text
32, 56, 68, 72
```

Reason:

- Candidate `32` is an entity/project subsidy, not a direct citizen aid.
- Candidate `56` is education-adjacent but grants funds to non-profit entities.
- Candidate `68` is a social assistance topic but grants funds to assistance institutions.
- Candidate `72` funds training plans through unions/business organizations and related entities.

## Needs More Evidence / PDF

No candidate needs PDF at this stage.

```text
needs_pdf=yes: none
```

XML/HTML evidence was sufficient to make an operational routing decision for all 13 candidates.

## Field Completeness Observations

For accepted candidates:

- Beneficiary information is present.
- Amount or budget information is present.
- Application deadline is present.
- Application channel or source application reference is present.
- Requirements are present at extract level.

For downstream use, full structured field extraction still needs a later downstream/staging task. This report is not a publication decision.

## Verification

Post-review checks:

| Item | Value |
|---|---:|
| `source_candidates` | 75 |
| `source_candidates.human_review_required` | 75 |
| Artifact directory size before review | 24M |
| Artifact directory size after review | 24M |
| PDF downloads during review | 0 |

DB validation:

```text
valid
```

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Known Limitations

- This is an operational evidence review, not legal advice.
- Decisions were not written to `candidate_evidence_reviews`; this report is the review artifact.
- No PDF was downloaded or reviewed.
- Downstream import has not been performed.
- `source_candidates.review_status` remains publication-safe and unchanged.

## Next Recommended Task

Recommended next task:

```text
TASK-005G - Apply selected 6-month evidence review decisions
```

Apply the operational evidence decisions safely to `candidate_evidence_reviews` only, keeping:

```text
source_candidates.review_status=human_review_required
```

Do not write downstream projects yet. After that, route only accepted candidates to the appropriate downstream staging flow.

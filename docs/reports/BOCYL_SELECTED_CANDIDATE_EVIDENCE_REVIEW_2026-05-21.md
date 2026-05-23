# BOCYL Selected Candidate Evidence Review - 2026-05-21

## Scope

This report records a metadata and stored XML/HTML evidence review for the 10
BOCYL candidates selected in `BOCYL-006` and downloaded in `BOCYL-007`.

Rules applied:

- no new artifacts were downloaded;
- no PDFs were downloaded;
- no candidates were created;
- no `source_candidates.review_status` values were changed;
- no downstream writes were performed;
- no EduAyudas work was performed;
- no `la-ayuda` work was performed;
- no approvals or publications were performed;
- no MCP surface was exposed.

## Context

Evidence download report:

```text
docs/reports/BOCYL_SELECTED_CANDIDATE_EVIDENCE_DOWNLOAD_2026-05-21.md
```

Selected candidates:

```text
126,128,129,131,134,138,141,142,145,146
```

BOCYL-007 evidence state:

```text
xml=10/10
html=10/10
pdf=0/10
raw_api_response=10/10
artifact_download_attempts=482
document_files=27120
source_candidates.review_status=human_review_required
```

Important audit note:

```text
artifact_download_attempts includes 20 historical BOCYL HTTP 302 failures from
the first controlled attempt and 20 successful XML/HTML attempts after redirect
support was added.
```

## Evidence Availability

All reviewed candidates have stored XML and HTML evidence, plus the original raw
API response. No reviewed candidate has downloaded PDF evidence.

| candidate_id | source | review_status | xml | html | pdf | integrity warning |
| ---: | --- | --- | --- | --- | --- | --- |
| 126 | BOCYL | human_review_required | yes | yes | no | absent |
| 128 | BOCYL | human_review_required | yes | yes | no | absent |
| 129 | BOCYL | human_review_required | yes | yes | no | absent |
| 131 | BOCYL | human_review_required | yes | yes | no | absent |
| 134 | BOCYL | human_review_required | yes | yes | no | absent |
| 138 | BOCYL | human_review_required | yes | yes | no | absent |
| 141 | BOCYL | human_review_required | yes | yes | no | absent |
| 142 | BOCYL | human_review_required | yes | yes | no | absent |
| 145 | BOCYL | human_review_required | yes | yes | no | absent |
| 146 | BOCYL | human_review_required | yes | yes | no | absent |

## Decision Distribution

| operational decision | count |
| --- | ---: |
| accept_for_downstream_pilot | 9 |
| needs_more_evidence | 1 |
| out_of_scope | 0 |
| false_positive | 0 |
| defer | 0 |
| total | 10 |

Downstream fit:

| downstream fit | count |
| --- | ---: |
| EduAyudas | 8 |
| both | 1 |
| unclear | 1 |
| la-ayuda | 0 |
| neither | 0 |

## Candidate Review

| id | official_identifier | decision | downstream_fit | beneficiary_type | direct aid | student/training | entity/project subsidy | scope | deadline | amount/budget | requirements | channel | documentation | reasoning |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 126 | `BOCYL:BOCYL-D-15052026-91-8` | accept_for_downstream_pilot | EduAyudas | university students | yes | yes | no | Universidad de Salamanca / rural practice placements | yes | yes | yes | yes | not explicit in extract | Campus Rural practice grants for degree/master students; XML/HTML include beneficiary, amount, deadline, and application channel. |
| 128 | `BOCYL:BOCYL-D-14052026-90-7` | needs_more_evidence | unclear | FP students indirectly | yes | yes | no | Castilla y Leon FP | not applicable | not explicit in extract | yes | not applicable | not applicable | This is a modification of regulatory bases, not a current application call; relevant for evidence context but not enough for a downstream pilot item by itself. |
| 129 | `BOCYL:BOCYL-D-13052026-89-10` | accept_for_downstream_pilot | EduAyudas | university students | yes | yes | no | Universidad de Valladolid | yes | present in full call reference / extract context | yes | yes | not explicit in extract | Becas Santander/Ayuda Economica for degree/master students; evidence includes BDNS reference, beneficiary and purpose. |
| 131 | `BOCYL:BOCYL-D-12052026-88-14` | accept_for_downstream_pilot | EduAyudas | master students | yes | yes | no | Universidad de Salamanca / Erasmus master studies | yes | yes | yes | not explicit in extract | not explicit in extract | Extraordinary Erasmus grants for master students; evidence includes beneficiaries, object, budget and deadline. |
| 134 | `BOCYL:BOCYL-D-11052026-87-8` | accept_for_downstream_pilot | EduAyudas | university students | yes | yes | no | Universidad de Burgos / international mobility | yes | yes | yes | not explicit in extract | not explicit in extract | Travel aid for UBU-Global international mobility students; evidence includes beneficiaries, purpose, budget and deadline. |
| 138 | `BOCYL:BOCYL-D-06052026-84-9` | accept_for_downstream_pilot | EduAyudas | university students | yes | yes | no | Universidad de Leon | yes | present in program context | yes | not explicit in extract | not explicit in extract | Ayuda Economica Santander for degree/master students; evidence includes beneficiaries, objective, requirements and long application window. |
| 141 | `BOCYL:BOCYL-D-04052026-82-17` | accept_for_downstream_pilot | EduAyudas | university students | yes | yes | no | Universidad de Leon / rural practice placements | likely in full call | yes | likely in full call | not explicit in extract | not explicit in extract | Campus Rural practice grants for university students; evidence confirms BDNS reference, beneficiary concept and grant amount. |
| 142 | `BOCYL:BOCYL-D-04052026-82-39` | accept_for_downstream_pilot | both | families with enrolled children | yes | yes | no | Province of Valladolid | yes | not in extract | yes | yes | not explicit in extract | Foundation Schola study aid for families schooling children; private foundation notice but published officially and clearly education-aid oriented. |
| 145 | `BOCYL:BOCYL-D-29042026-80-7` | accept_for_downstream_pilot | EduAyudas | university master students | yes | yes | no | Universidad de Salamanca / China master mobility | yes | likely in full call | yes | not explicit in extract | not explicit in extract | Scholarships for master studies in Chinese universities; evidence includes beneficiaries, object, BDNS reference and deadline. |
| 146 | `BOCYL:BOCYL-D-21042026-75-8` | accept_for_downstream_pilot | EduAyudas | university degree/master students | yes | yes | no | Universidad de Burgos | yes | yes | yes | not explicit in extract | not explicit in extract | Becas Santander/Ayuda Economica for degree/master students; evidence includes beneficiaries, amount, requirements and deadline. |

## Accepted For Downstream Pilot

Recommended for a controlled downstream pilot in a later explicit task:

```text
126,129,131,134,138,141,142,145,146
```

Routing:

| route | candidate_ids |
| --- | --- |
| EduAyudas | `126,129,131,134,138,141,145,146` |
| both | `142` |

Do not write downstream as part of this review.

## Needs More Evidence

```text
128
```

Reason:

```text
The evidence is a regulatory-bases modification for complementary FP mobility
aid. It is relevant context but not an actionable call/extract by itself. Use it
as supporting evidence only if a later concrete call references the amended
bases.
```

## Out Of Scope

```text
none
```

## False Positives

```text
none among the 10 selected candidates
```

The false-positive families found in `BOCYL-006` were already excluded from this
download/review set.

## Deferred

```text
none
```

## Status Verification

Post-review checks:

```text
source_candidates=146
artifact_download_attempts=482
document_files=27120
review_status_distribution=human_review_required:146
selected_review_status_distribution=human_review_required:10
artifact_dir_size=30M
db_validate=valid
mcp_privacy_check=no official/mcp/python/uvicorn/fastmcp listener found
```

No state-changing operation was intentionally performed during this review.

## Known Limitations

This review uses stored BOCYL XML/HTML extracts and metadata. Several records
point to BDNS for the complete call text; if a downstream pilot requires full
application form fields or exhaustive documentation lists, BDNS detail evidence
should be inspected in a separate scoped task.

PDFs remain intentionally undownloaded. XML/HTML were enough for the operational
classification in this pass.

Candidate 128 should not be routed as a standalone downstream item until it is
paired with a concrete call.

## Next Recommended Task

```text
TASK-AUTO-BOCYL-009 - Apply BOCYL evidence review decisions
```

Scope recommendation:

- write review decisions only into `candidate_evidence_reviews`;
- keep `source_candidates.review_status=human_review_required`;
- do not write downstream;
- do not approve or publish;
- include a pre/post DB validation and status count report.

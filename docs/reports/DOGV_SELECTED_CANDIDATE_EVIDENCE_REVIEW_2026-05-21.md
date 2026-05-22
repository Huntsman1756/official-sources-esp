# DOGV Selected Candidate Evidence Review - 2026-05-21

## Summary

TASK-AUTO-DOGV-008 reviewed the downloaded DOGV PDF evidence for the 10 selected candidates.

This was evidence review only. No downstream project was touched. No candidates were created.
`source_candidates.review_status` was not changed. Nothing was approved or published. No new PDFs
were downloaded. No DOGV backfill was run. MCP exposure was unchanged.

## Deployed State

```text
vps_checkout_commit=e0784f7
local_main_before_report=5ed0c3da9fed1ab7b87fc7cc004334b44b99236b
database=/opt/official-sources/data/official_sources.sqlite
db_validation=current_version=8 latest_version=8 status=valid
```

Relevant prior reports:

```text
docs/reports/DOGV_SCOPED_ARTIFACT_DOWNLOADER_2026-05-21.md
docs/reports/DOGV_SELECTED_CANDIDATE_EVIDENCE_DOWNLOAD_RETRY_2026-05-21.md
```

## Evidence Availability

```text
candidates_reviewed=10
candidate_ids=101,102,103,104,106,108,109,111,117,124
source_code=DOGV for all reviewed candidates
review_status=human_review_required for all reviewed candidates
pdf_available=10/10
pdf_file_hash_present=10/10
integrity_warning=0/10
```

State before and after review:

```text
artifact_download_attempts=442 -> 442
document_files_total=26015 -> 26015
DOGV_pdf_document_files=10 -> 10
selected_pdf_document_files=10 -> 10
artifact_directory_size=30M -> 30M
source_candidates_total=125 -> 125
review_status_distribution=human_review_required:125 -> human_review_required:125
selected_review_status_distribution=human_review_required:10 -> human_review_required:10
```

## Decision Distribution

| decision | count |
| --- | ---: |
| `accept_for_downstream_pilot` | 10 |
| `needs_more_evidence` | 0 |
| `out_of_scope` | 0 |
| `false_positive` | 0 |
| `defer` | 0 |

## Evidence Review Table

| id | identifier | issuer_or_department | beneficiary_type | direct aid | student/training | entity/project subsidy | deadline | amount/budget | requirements | channel | docs required | downstream_fit | decision | reasoning |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 101 | `DOGV:DOGV-C-2026-16062` | Universitat Politecnica de Valencia | Master's students | yes | yes | no | yes | yes | yes | referenced in bases | not in extract | EduAyudas | `accept_for_downstream_pilot` | PDF evidence identifies student beneficiaries, study aid, amount, deadline, and bases. |
| 102 | `DOGV:DOGV-C-2026-16067` | Universitat Politecnica de Valencia | Master's students in external international practice | yes | yes | no | yes | yes | yes | referenced in bases | not in extract | EduAyudas | `accept_for_downstream_pilot` | Direct training/practice scholarship with travel and monthly support elements. |
| 103 | `DOGV:DOGV-C-2026-16321` | Universidad de Alicante | University students | yes | yes | no | yes | yes | yes | BOUA/bases referenced | not in extract | EduAyudas | `accept_for_downstream_pilot` | Paid university practice scholarship; evidence shows students as beneficiaries and call details. |
| 104 | `DOGV:DOGV-C-2026-15641` | Universitat Jaume I de Castello | University students / physical persons | yes | yes | no | yes | yes | yes | university office/bases referenced | not in extract | EduAyudas | `accept_for_downstream_pilot` | Individual research-initiation scholarship with person-level eligibility and amount. |
| 106 | `DOGV:DOGV-C-2026-15801` | Universidad de Alicante | Degree/master/doctoral students | yes | yes | no | yes | yes | yes | BOUA/bases referenced | not in extract | EduAyudas | `accept_for_downstream_pilot` | Foreign research stay aid directed to alumnado with budget, deadline, and bases. |
| 108 | `DOGV:DOGV-C-2026-15504` | Universidad de Alicante | University students | yes | yes | no | yes | yes | yes | BOUA/bases referenced | not in extract | EduAyudas | `accept_for_downstream_pilot` | Mobility aid for students under Erasmus+/Aitana practice program. |
| 109 | `DOGV:DOGV-C-2026-15505` | Universidad de Alicante | Polytechnic school students | yes | yes | no | yes | yes | yes | BOUA/bases referenced | not in extract | EduAyudas | `accept_for_downstream_pilot` | Direct international mobility aid for students with amount and application period. |
| 111 | `DOGV:DOGV-C-2026-14623` | Conselleria de Educacion, Cultura y Universidades | Students completing university studies | yes | yes | no | yes | yes | yes | telematic application | not in extract | EduAyudas | `accept_for_downstream_pilot` | Generalitat scholarship for students near degree completion; evidence includes telematic deadline and budget. |
| 117 | `DOGV:DOGV-C-2026-14923` | Labora Servicio Valenciano de Empleo y Formacion | Workers affected by EREs | yes | no | no | yes | yes | yes | referenced in governing order | not in extract | la-ayuda | `accept_for_downstream_pilot` | Direct worker support line, not education-specific; fits general citizen aid routing. |
| 124 | `DOGV:DOGV-C-2026-14022` | Universidad de Alicante | University students participating in linguistic volunteering | yes | yes | no | yes | yes | yes | BOUA/bases referenced | not in extract | EduAyudas | `accept_for_downstream_pilot` | Student aid for university linguistic volunteering with budget and deadlines. |

Notes:

```text
application_channel_present means the PDF evidence identifies a submission route or references the official bases/source where the route is defined.
documentation_required_present is mostly absent from these DOGV extracts and should be checked in full bases during downstream enrichment.
```

## Accepted For Downstream Pilot

Accepted candidates:

```text
101,102,103,104,106,108,109,111,117,124
```

Primary routing:

```text
EduAyudas: 101,102,103,104,106,108,109,111,124
la-ayuda: 117
```

Rationale:

```text
The nine EduAyudas candidates are direct student, scholarship, study, mobility, practice, or training aids.
Candidate 117 is direct worker support and fits la-ayuda better than EduAyudas.
```

## Other Decision Buckets

Needs more evidence:

```text
none
```

Out of scope:

```text
none
```

False positives:

```text
none
```

Deferred:

```text
none
```

## Operational Observations

The selected DOGV evidence quality is stronger than the metadata-only triage suggested. The 10 PDFs
are official one- or two-page DOGV extracts that consistently expose:

```text
beneficiary or eligible-person class
object/purpose of the aid
regulatory bases or source where bases are published
amount or global budget
application deadline or deadline rule
```

Limitations:

```text
Most extracts do not include full documentation requirements.
Several university calls delegate full details to BOUA or university bases.
Downstream publication should wait for a later task that records decisions and, if needed, retrieves scoped full bases.
```

No full PDF text or raw extracted text is stored in this report.

## Safety Verification

Post-review checks:

```text
source_candidates_total=125
DOGV_candidates_total=25
review_status_distribution=human_review_required:125
selected_review_status_distribution=human_review_required:10
artifact_download_attempts=442
document_files_total=26015
DOGV_pdf_document_files=10
selected_pdf_document_files=10
artifact_directory_size=30M
db_validation=current_version=8 latest_version=8 status=valid
```

MCP privacy check:

```text
command=ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
result=no matching listener reported
```

## Recommended Next Task

```text
TASK-AUTO-DOGV-009 - Apply DOGV evidence review decisions
```

Recommended scope:

```text
write candidate_evidence_reviews only
candidate_ids=101,102,103,104,106,108,109,111,117,124
decision=accept_for_downstream_pilot
downstream_fit_EduAyudas=101,102,103,104,106,108,109,111,124
downstream_fit_la-ayuda=117
keep source_candidates.review_status=human_review_required
no downstream writes
no approval
no publication
```

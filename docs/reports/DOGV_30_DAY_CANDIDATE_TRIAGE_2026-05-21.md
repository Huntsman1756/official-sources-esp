# DOGV 30-Day Candidate Triage - 2026-05-21

## Summary

TASK-AUTO-DOGV-006 reviewed the 25 DOGV candidates created in TASK-AUTO-DOGV-005.

This was metadata-only triage. No PDFs, XML, HTML, or other artifacts were downloaded. No DOGV live
API was called. No new candidates were created. `source_candidates.review_status` was not changed.
No downstream project was touched. Nothing was approved or published. MCP exposure was unchanged.

## State Reviewed

```text
vps_checkout_commit=55170ee
local_main_before_report=303b5a099ef6495140f004e88a224fa8d4130f16
database=/opt/official-sources/data/official_sources.sqlite
db_validation_before=current_version=8 latest_version=8 status=valid
```

The VPS checkout was on the DOGV profile code commit used for candidate creation. The later local
commits were report-only and were not required for metadata triage.

## Scope

```text
source=DOGV
candidate_ids=101..125
candidates_reviewed=25
mode=metadata_only
artifact_downloads=none
downstream_writes=none
```

Fields reviewed per candidate:

```text
candidate_id
source_code
official_identifier
publication_date
title
department
official_url
matched_keywords
score
score_reasons
review_status
```

## Pre-Triage Verification

```text
source_candidates_total_before=125
DOGV_source_candidates_before=25
review_status_distribution_before=human_review_required:125
DOGV_review_status_distribution_before=human_review_required:25
artifact_download_attempts_before=432
artifact_directory_size_before=26M
```

## Triage Distribution

| triage_label | count |
| --- | ---: |
| `likely_relevant` | 16 |
| `unclear` | 2 |
| `out_of_scope` | 5 |
| `false_positive` | 2 |

## Candidate Triage Table

| id | identifier | title summary | matched_keywords | score | triage_label | triage_reason | recommended_evidence_action |
| ---: | --- | --- | --- | ---: | --- | --- | --- |
| 101 | `DOGV:DOGV-C-2026-16062` | Becas de ayuda para estudiar master de Ingenieria de Caminos. | becas, ayuda, subvenciones | 6 | `likely_relevant` | Direct student scholarship. | `download_pdf` |
| 102 | `DOGV:DOGV-C-2026-16067` | Becas para practicas externas internacionales en master de Cooperacion al Desarrollo. | becas, subvenciones | 4 | `likely_relevant` | Student/training scholarship. | `download_pdf` |
| 103 | `DOGV:DOGV-C-2026-16321` | Practicas becadas en Departamento de Ecologia, Universidad de Alicante. | becas, subvenciones, universidad | 6 | `likely_relevant` | Paid university practice opportunity. | `download_pdf` |
| 104 | `DOGV:DOGV-C-2026-15641` | Beca de iniciacion a la investigacion en proyecto universitario. | beca, becas, subvenciones, convocatoria | 7 | `likely_relevant` | Individual university research scholarship. | `download_pdf` |
| 105 | `DOGV:DOGV-C-2026-15642` | Beca de iniciacion a investigacion with bridge aid wording for research projects. | beca, becas, subvenciones, convocatoria | 7 | `unclear` | Looks like a scholarship, but wording suggests project support. | `needs_human_title_review` |
| 106 | `DOGV:DOGV-C-2026-15801` | Ayudas Banco Santander-UA for foreign research stays for alumnado. | becas, ayudas, subvenciones, alumnado, universidad | 10 | `likely_relevant` | Direct aid for students. | `download_pdf` |
| 107 | `DOGV:DOGV-C-2026-15376` | Resolved sports grants for nonprofit sport entities. | becas, subvenciones, convocatoria, convocatoria de subvenciones | 8 | `out_of_scope` | Entity subsidy and resolved call, not direct citizen/student aid. | `do_not_download` |
| 108 | `DOGV:DOGV-C-2026-15504` | Mobility aid for University of Alicante students. | becas, ayudas, subvenciones, estudiantes, universidad | 10 | `likely_relevant` | Direct student mobility aid. | `download_pdf` |
| 109 | `DOGV:DOGV-C-2026-15505` | Ayudas para estudiantes of EPS doing international mobility. | becas, ayudas, subvenciones, ayudas para estudiantes, estudiantes, universidad | 13 | `likely_relevant` | Strong direct student aid. | `download_pdf` |
| 110 | `DOGV:DOGV-C-2026-13949` | Becas for alumnado completing university studies. | becas, subvenciones, alumnado, universidades | 8 | `likely_relevant` | Direct student scholarship. | `defer` |
| 111 | `DOGV:DOGV-C-2026-14623` | Extract for the same university-completion scholarship line. | becas, subvenciones, alumnado, universidades | 8 | `likely_relevant` | Direct student scholarship; extract is better evidence target than paired resolution. | `download_pdf` |
| 112 | `DOGV:DOGV-C-2026-14721` | Beca de iniciacion a investigacion on adult osteoporosis project. | beca, becas, subvenciones, convocatoria | 7 | `likely_relevant` | Individual research scholarship, but narrower than top evidence picks. | `defer` |
| 113 | `DOGV:DOGV-C-2026-14724` | Several research initiation scholarships linked to a university project. | becas, subvenciones, convocatoria | 5 | `likely_relevant` | Individual scholarship wording, lower priority. | `defer` |
| 114 | `DOGV:DOGV-C-2026-14727` | Complementary research-project aid for projects captured by research staff. | beca, becas, subvenciones, convocatoria | 7 | `out_of_scope` | Project/research group support, not direct citizen/student aid. | `do_not_download` |
| 115 | `DOGV:DOGV-C-2026-14728` | Aid for associationism and participation in university community. | becas, ayudas, subvenciones | 6 | `unclear` | Could be student/community aid but may target associations/groups. | `needs_human_title_review` |
| 116 | `DOGV:DOGV-C-2026-14803` | Credit line for additional aid to workers affected by EREs. | becas, ayudas, subvenciones, empleo, formacion | 8 | `likely_relevant` | Direct worker support, but paired with extract. | `defer` |
| 117 | `DOGV:DOGV-C-2026-14923` | Extract of additional aid to workers affected by EREs. | becas, ayudas, subvenciones, empleo, formacion | 8 | `likely_relevant` | Direct worker support; extract is preferred evidence target. | `download_pdf` |
| 118 | `DOGV:DOGV-C-2026-14421` | Subsidies for employment of people with disabilities in special employment centers. | becas, subvenciones, empleo, formacion, discapacidad | 8 | `out_of_scope` | Employer/center subsidy, not direct person aid. | `do_not_download` |
| 119 | `DOGV:DOGV-C-2026-14422` | Correction of errors for UPV student social-action aid call. | becas, ayudas, subvenciones, convocatoria, convocatoria de ayudas, estudiantes | 12 | `likely_relevant` | Underlying aid is relevant, but this is a correction notice. | `defer` |
| 120 | `DOGV:DOGV-C-2026-14423` | Public subsidies for employment of people with disabilities in CEE. | becas, subvenciones, empleo, formacion, discapacidad | 8 | `out_of_scope` | Employer/center subsidy, not direct person aid. | `do_not_download` |
| 121 | `DOGV:DOGV-C-2026-14522` | Authorization of schedule-coordination program for students taking simultaneous studies. | alumnado, universidades | 4 | `false_positive` | Education administration authorization, not aid/support. | `do_not_download` |
| 122 | `DOGV:DOGV-C-2026-14542` | Call for two research initiation scholarships in IT department. | becas, subvenciones, convocatoria | 5 | `likely_relevant` | Individual scholarship wording, lower priority. | `defer` |
| 123 | `DOGV:DOGV-C-2026-14483` | Authorization of school assignment/adscription for private schools. | alumnado, universidades | 4 | `false_positive` | School administration notice, not aid/support. | `do_not_download` |
| 124 | `DOGV:DOGV-C-2026-14022` | Ayudas for linguistic volunteering at University of Alicante. | becas, ayudas, subvenciones, universidad, formacion | 9 | `likely_relevant` | Direct university aid related to student/community participation. | `download_pdf` |
| 125 | `DOGV:DOGV-C-2026-13405` | Subsidies for university sport and CADU organization. | becas, subvenciones | 4 | `out_of_scope` | Institutional/event subsidy, not direct student aid. | `do_not_download` |

## Selected Evidence Candidates

Selected for a future evidence-download task, capped at 10:

```text
101
102
103
104
106
108
109
111
117
124
```

Selection rationale:

```text
clear direct scholarship/student aid wording
good coverage across scholarship, mobility, study, student support, and worker support
extract notices preferred when paired with a full resolution
known noisy/entity-only items excluded
correction/procedural notices deferred
```

No evidence was downloaded in this task.

## Examples

Likely relevant examples:

```text
101 - becas de ayuda para estudiar master
106 - ayudas for foreign research stays directed to alumnado
109 - ayudas para estudiantes for international mobility
111 - becas for alumnado completing university studies
117 - additional aid to workers affected by EREs
124 - ayudas for university linguistic volunteering
```

Unclear examples:

```text
105 - scholarship wording mixed with research-project support wording
115 - university community associationism aid may target groups rather than individuals
```

Out-of-scope examples:

```text
107 - resolved sport-entity subsidies
118 / 120 - subsidies to special employment centers
125 - subsidies for sport organization/event activity
```

False positives:

```text
121 - education scheduling authorization
123 - school assignment/adscription authorization
```

## Noise Observations

The refined profile successfully limited the candidate batch, but DOGV metadata still surfaces some
expected review noise:

```text
paired resolution/extract notices for the same aid line
research-project scholarship wording that needs human review
entity or event subsidies under the same SUBVENCIONES Y BECAS section
education administrative notices matching alumnado/universidad terms
employment/disability subsidies that may support people indirectly through institutions
```

For the next stage, evidence collection should prefer official PDF for the selected candidates unless
DOGV HTML or XML proves more stable and complete for structured extraction.

## Post-Triage Verification

No database state was intentionally changed. Verification after metadata extraction:

```text
source_candidates_total_after=125
DOGV_source_candidates_after=25
review_status_distribution_after=human_review_required:125
DOGV_review_status_distribution_after=human_review_required:25
artifact_download_attempts_after=432
artifact_directory_size_after=26M
db_validation_after=current_version=8 latest_version=8 status=valid
```

MCP privacy check:

```text
command=ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
result=no matching listener reported
```

## Next Recommended Task

```text
TASK-AUTO-DOGV-007 - DOGV selected candidate evidence download
```

Recommended scope:

```text
candidate_ids=101,102,103,104,106,108,109,111,117,124
mode=scoped_evidence_only
preferred_evidence_to_confirm_before_download=official_pdf
no_downstream_writes=true
no_approval=true
no_publication=true
```

Before downloading anything, confirm which DOGV evidence source is preferred:

```text
PDF oficial
HTML publico
XML dinamico
metadata JSON detalle
```

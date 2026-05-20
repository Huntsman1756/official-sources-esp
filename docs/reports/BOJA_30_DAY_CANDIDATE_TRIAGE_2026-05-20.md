# BOJA 30-Day Candidate Triage - 2026-05-20

## Summary

TASK-AUTO-006 reviewed the 25 BOJA `source_candidates` created in TASK-AUTO-005.

This was metadata-only triage. No PDFs, XML, or HTML artifacts were downloaded. No candidates were approved, published, or written downstream.

## Deployed State

VPS application path:

```text
/opt/official-sources/app
```

Operational deployed commit:

```text
2ab44f0
```

Database validation before triage:

```text
current_version=8
latest_version=8
status=valid
```

## Candidate Batch Reviewed

Selection:

```text
source=BOJA
candidate_count=25
candidate_ids=76-100
review_status=human_review_required
evidence_level=metadata_keyword_match
```

Pre-triage state:

```text
source_candidates_total=100
BOJA source_candidates=25
artifact_download_attempts=392
artifact_directory_size=24M
```

## Triage Distribution

| triage_label | count |
| --- | ---: |
| likely_relevant | 9 |
| unclear | 10 |
| out_of_scope | 1 |
| false_positive | 5 |

## Selected Evidence Candidates

Selected for future scoped evidence download:

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

These were selected because they are the strongest scholarship, student, education, training, or youth-support signals in the metadata batch, plus one high-value unclear FPE notification representative.

Do not download evidence broadly. TASK-AUTO-007 should first verify which BOJA evidence fields are available for these candidates and then download only scoped evidence for selected IDs.

## Triage Table

| candidate_id | official_identifier | date | issuer_or_department | title summary | keywords | score | triage_label | triage_reason | recommended_evidence_action |
| ---: | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| 76 | `BOJA:disposition.2026.95.21` | 2026-05-20 | Sanidad, Presidencia y Emergencias | Public employment selection lists for cleaning staff reserved for intellectual disability access. | discapacidad | 2 | false_positive | Disability keyword is incidental; this is a personnel selection notice, not an aid/scholarship/support program. | do_not_download |
| 77 | `BOJA:disposition.2026.95.6` | 2026-05-20 | Universidades | University of Huelva talent-attraction scholarships for Master's students. | becas, estudiantes | 4 | likely_relevant | Clear scholarship/student wording and likely useful for education-aid review. | download_pdf |
| 78 | `BOJA:disposition.2026.94.5` | 2026-05-19 | Universidades | University of Huelva aid for university students doing external academic internships under Campus Rural. | ayudas, estudiantes | 4 | likely_relevant | Clear direct student aid wording. | download_pdf |
| 79 | `BOJA:disposition.2026.93.28` | 2026-05-18 | Universidades | Resolution of six library training scholarships at Universidad Pablo de Olavide. | becas, convocatoria | 3 | likely_relevant | Clear scholarship/training wording, although it may be a resolved call rather than a new open call. | download_pdf |
| 80 | `BOJA:disposition.2026.92.1` | 2026-05-15 | Desarrollo Educativo y Formacion Profesional | EU stays for students in Vocational Training and Arts/Design studies. | convocatoria, alumnado | 3 | likely_relevant | Clear student and education mobility signal. | download_pdf |
| 81 | `BOJA:disposition.2026.92.55` | 2026-05-15 | Fomento, Territorio y Vivienda | Notices for rent aid to vulnerable people, limited-income households, and young people. | ayudas, convocatoria, vivienda, alquiler, jovenes | 9 | likely_relevant | Not EduAyudas-specific, but plausibly useful for la-ayuda style support discovery. | download_pdf |
| 82 | `BOJA:disposition.2026.91.73` | 2026-05-14 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where a scholarship resolution could not be notified. | beca, ayuda | 4 | unclear | It appears to involve training aid, but it is a procedural notification list. | download_pdf |
| 83 | `BOJA:disposition.2026.91.74` | 2026-05-14 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where scholarship request correction could not be notified. | beca, ayuda | 4 | unclear | Training aid signal exists, but the notice is procedural and may not define a reusable aid program. | defer |
| 84 | `BOJA:disposition.2026.91.75` | 2026-05-14 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where provisional scholarship resolution could not be notified. | beca, ayuda | 4 | unclear | Training aid signal exists, but metadata suggests procedural notification. | defer |
| 85 | `BOJA:disposition.2026.91.86` | 2026-05-14 | Ayuntamientos | Municipal employment selection process for posts reserved for people with disability. | bases reguladoras, discapacidad | 5 | false_positive | This is an employment selection notice, not an aid program. | do_not_download |
| 86 | `BOJA:disposition.2026.90.5` | 2026-05-13 | Universidades | 100 Santander economic-aid scholarships for degree and master's students. | becas, ayuda, estudiantes | 6 | likely_relevant | Strong scholarship, aid, and student wording. | download_pdf |
| 87 | `BOJA:disposition.2026.89.44` | 2026-05-12 | Universidades | Resolution of a training scholarship linked to a Faculty of Social Sciences program. | beca, convocatoria, estudiantes | 5 | likely_relevant | Student/training scholarship signal, though likely a resolved call. | download_pdf |
| 88 | `BOJA:disposition.2026.87.13` | 2026-05-08 | Universidades | Resolution of a scholarship linked to academic planning, official degrees, and quality. | beca, convocatoria | 3 | unclear | Scholarship signal is real, but metadata suggests a resolved internal university scholarship. | defer |
| 89 | `BOJA:disposition.2026.87.64` | 2026-05-08 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where scholarship resolution could not be notified. | beca, ayuda | 4 | unclear | Procedural FPE notification; may duplicate candidate 82 pattern. | defer |
| 90 | `BOJA:disposition.2026.87.65` | 2026-05-08 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where scholarship resolution could not be notified. | beca, ayuda | 4 | unclear | Procedural FPE notification; likely duplicate pattern. | defer |
| 91 | `BOJA:disposition.2026.87.66` | 2026-05-08 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where archive by withdrawal of scholarship applications could not be notified. | becas, ayudas | 4 | unclear | Real FPE aid wording, but likely procedural case handling rather than program definition. | defer |
| 92 | `BOJA:disposition.2026.87.68` | 2026-05-08 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where provisional scholarship resolution could not be notified. | beca, ayuda | 4 | unclear | Procedural FPE notification; likely duplicate pattern. | defer |
| 93 | `BOJA:disposition.2026.86.57` | 2026-05-07 | Universidades | Resolution of a training scholarship linked to the equality office. | beca | 2 | likely_relevant | Real university training scholarship signal; evidence can confirm whether useful downstream. | download_pdf |
| 94 | `BOJA:disposition.2026.86.71` | 2026-05-07 | Empleo, Empresa y Trabajo Autonomo | Notice for FPE aid applicants where archive resolution of scholarship file could not be notified. | becas, ayudas | 4 | unclear | Procedural FPE notification; likely duplicate pattern. | defer |
| 95 | `BOJA:disposition.2026.85.1` | 2026-05-06 | Empleo, Empresa y Trabajo Autonomo | Expanded credit for employment subsidies for people with disability in special employment centers and ordinary labor market. | subvenciones, bases reguladoras, convocatoria, convocatoria de subvenciones, discapacidad | 11 | out_of_scope | Real subsidy, but aimed at employment/companies/centers rather than EduAyudas/la-ayuda direct aid scope. | do_not_download |
| 96 | `BOJA:disposition.2026.84.26` | 2026-05-05 | Justicia, Administracion Local y Funcion Publica | Provisional admitted/excluded lists for public employment vacancies reserved for intellectual disability. | discapacidad | 2 | false_positive | Public employment process, not an aid. | do_not_download |
| 97 | `BOJA:disposition.2026.82.16` | 2026-04-30 | Universidad, Investigacion e Innovacion | Result of election of a university Social Council member by the student council. | estudiantes | 2 | false_positive | Student keyword is incidental; no aid/support program. | do_not_download |
| 98 | `BOJA:disposition.2026.81.46` | 2026-04-29 | Universidades | Resolution of two Santander-linked sport talent training scholarships. | becas | 2 | likely_relevant | Scholarship wording and student/sport talent context look useful for evidence review. | download_pdf |
| 99 | `BOJA:disposition.2026.81.59` | 2026-04-29 | Inclusion Social, Juventud, Familias e Igualdad | Notification of disability-degree recognition resolutions. | discapacidad | 2 | false_positive | Administrative disability recognition, not an aid candidate. | do_not_download |
| 100 | `BOJA:disposition.2026.80.42` | 2026-04-28 | Fomento, Territorio y Vivienda | Notices for justification/reimbursement proceedings for rent aid to vulnerable people and young people. | ayudas, convocatoria, vivienda, alquiler, jovenes | 9 | unclear | Real aid context, but this is a justification/reimbursement notice rather than a clean program/call. | defer |

## Likely Relevant Examples

- Candidate 77: Master's scholarship/student wording.
- Candidate 78: student internship aid wording.
- Candidate 80: education mobility/stays for vocational and arts/design students.
- Candidate 86: economic-aid scholarships for university students.
- Candidate 98: sport talent training scholarships.

## Unclear Examples

- Candidates 82, 83, 84, 89, 90, 91, 92, and 94: repeated FPE aid/scholarship notification patterns. They may point to useful training aid programs, but the metadata is procedural.
- Candidate 100: youth/vulnerable rent aid context, but the title indicates justification or reimbursement proceedings.

## Out Of Scope

- Candidate 95: employment subsidies for people with disability in employment centers or the labor market. It is a real subsidy but not a direct EduAyudas/la-ayuda candidate from metadata alone.

## False Positives

- Candidate 76: public employment selection list.
- Candidate 85: municipal employment selection process.
- Candidate 96: public employment admission/exclusion list.
- Candidate 97: university governance election result.
- Candidate 99: disability-degree recognition notification.

## Noise Observations

- The `discapacidad` keyword catches both potentially useful social-support notices and irrelevant public-employment or administrative-recognition records.
- FPE aid/scholarship notices are common and often procedural. One representative should be inspected before broad evidence download.
- Housing/rent notices can fit la-ayuda but may be procedural rather than a clean call.
- University scholarship notices look like the highest-value BOJA metadata class for the next evidence step.

## Post-Triage Safety Verification

No operational triage labels were written to the database in this task.

```text
source_candidates_total=100
BOJA source_candidates=25
review_status_distribution=human_review_required:100
BOJA review_status_distribution=human_review_required:25
artifact_download_attempts=392
artifact_directory_size=24M
DB validation=status=valid
```

MCP/privacy check:

```text
ss checks for official, mcp, python, uvicorn, and fastmcp returned no matching listeners.
```

## Known Limitations

- This triage is metadata-only and not an approval decision.
- BOJA candidate rows did not expose direct public/PDF URLs in the candidate metadata query used for this report. TASK-AUTO-007 must verify the available BOJA evidence fields before downloading.
- No scoped BOJA evidence download command was exercised in this task.
- FPE procedural notices may require a separate policy decision: inspect one representative first, then decide whether to keep or suppress the pattern.

## Recommendation

Recommended next task:

```text
TASK-AUTO-007 - BOJA selected candidate evidence download
```

Scope should be limited to:

```text
candidate_ids=77,78,79,80,81,82,86,87,93,98
```

Before downloading PDFs, verify whether BOJA offers a stable official public page, JSON detail endpoint, or PDF path for each selected document. Do not run broad artifact downloads.

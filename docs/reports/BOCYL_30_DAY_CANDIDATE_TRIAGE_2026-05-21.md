# BOCYL 30-Day Candidate Triage - 2026-05-21

## Scope

This report records a metadata-only triage of the 21 BOCYL candidates created in
`BOCYL-005`.

Rules applied:

- no PDF/XML/HTML artifacts were downloaded;
- no candidates were created;
- no `source_candidates.review_status` values were changed;
- no downstream writes were performed;
- no EduAyudas work was performed;
- no `la-ayuda` work was performed;
- no MCP surface was exposed;
- no candidates were approved or published.

## Context

Previous reports:

```text
docs/reports/BOCYL_30_DAY_CANDIDATE_BATCH_2026-05-21.md
docs/reports/PARALLEL_SOURCE_WORK_INTEGRATION_2026-05-21.md
```

BOCYL candidate batch:

```text
source_candidates: 125 -> 146
BOCYL candidates: 0 -> 21
artifact_download_attempts: 442 -> 442
artifacts: 30M -> 30M
DB valid
```

## VPS Read-Only Checks

Database validation before triage:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

Candidate and artifact counts observed during triage:

```text
BOCYL candidates=21
source_candidates_total=146
artifact_download_attempts=442
artifact_dir_size=30M
review_status_distribution=human_review_required:146
```

## Triage Distribution

| triage label | count |
| --- | ---: |
| likely_relevant | 10 |
| unclear | 3 |
| out_of_scope | 3 |
| false_positive | 5 |
| total | 21 |

Evidence actions:

| recommended evidence action | count |
| --- | ---: |
| download_xml_or_html | 10 |
| needs_human_title_review | 3 |
| do_not_download | 8 |
| total | 21 |

## Candidate Triage

| candidate_id | official_identifier | date | triage | evidence action | reason |
| ---: | --- | --- | --- | --- | --- |
| 126 | `BOCYL:BOCYL-D-15052026-91-8` | 2026-05-15 | likely_relevant | download_xml_or_html | 30 becas para estudiantes de la Universidad de Salamanca, Programa Campus Rural. |
| 127 | `BOCYL:BOCYL-D-15052026-91-9` | 2026-05-15 | unclear | needs_human_title_review | Becas Erasmus para BIP/summer school; title does not clearly state student recipient. |
| 128 | `BOCYL:BOCYL-D-14052026-90-7` | 2026-05-14 | likely_relevant | download_xml_or_html | Ayudas complementarias para alumnado de FP beneficiario de Erasmus+. |
| 129 | `BOCYL:BOCYL-D-13052026-89-10` | 2026-05-13 | likely_relevant | download_xml_or_html | Becas Santander Ayuda Economica para estudiantes de grado y master. |
| 130 | `BOCYL:BOCYL-D-13052026-89-9` | 2026-05-13 | false_positive | do_not_download | Becas Erasmus para personal docente e investigador. |
| 131 | `BOCYL:BOCYL-D-12052026-88-14` | 2026-05-12 | likely_relevant | download_xml_or_html | Becas Erasmus para realizar estudios de Master. |
| 132 | `BOCYL:BOCYL-D-12052026-88-15` | 2026-05-12 | false_positive | do_not_download | Becas Erasmus para PDI. |
| 133 | `BOCYL:BOCYL-D-11052026-87-10` | 2026-05-11 | unclear | needs_human_title_review | Resuelve ayudas al estudio; relevant topic but likely award/resolution state. |
| 134 | `BOCYL:BOCYL-D-11052026-87-8` | 2026-05-11 | likely_relevant | download_xml_or_html | Ayudas de viaje para estudiantes de movilidad internacional. |
| 135 | `BOCYL:BOCYL-D-11052026-87-9` | 2026-05-11 | unclear | needs_human_title_review | Becas de colaboracion y formacion; recipient fit needs confirmation. |
| 136 | `BOCYL:BOCYL-D-08052026-86-10` | 2026-05-08 | false_positive | do_not_download | Concurso-oposicion laboral con plazas de discapacidad intelectual. |
| 137 | `BOCYL:BOCYL-D-07052026-85-22` | 2026-05-07 | out_of_scope | do_not_download | Servicio de atencion y cuidado del alumnado; not an aid/call candidate from title. |
| 138 | `BOCYL:BOCYL-D-06052026-84-9` | 2026-05-06 | likely_relevant | download_xml_or_html | Ayuda Economica Santander para estudiantes de grado/master. |
| 139 | `BOCYL:BOCYL-D-05052026-83-15` | 2026-05-05 | out_of_scope | do_not_download | Seleccion de centros para programa de inmersion; not direct citizen/student aid. |
| 140 | `BOCYL:BOCYL-D-05052026-83-17` | 2026-05-05 | false_positive | do_not_download | Servicios esenciales en centros docentes; no aid/call signal. |
| 141 | `BOCYL:BOCYL-D-04052026-82-17` | 2026-05-04 | likely_relevant | download_xml_or_html | Becas Campus Rural para practicas universitarias. |
| 142 | `BOCYL:BOCYL-D-04052026-82-39` | 2026-05-04 | likely_relevant | download_xml_or_html | Fundacion Schola, ayudas al estudio para curso 2026-2027. |
| 143 | `BOCYL:BOCYL-D-04052026-82-5` | 2026-05-04 | false_positive | do_not_download | Tribunal de proceso selectivo para plazas de discapacidad intelectual. |
| 144 | `BOCYL:BOCYL-D-30042026-81-16` | 2026-04-30 | out_of_scope | do_not_download | Premios del Consejo de Estudiantes; not aid/subsidy evidence. |
| 145 | `BOCYL:BOCYL-D-29042026-80-7` | 2026-04-29 | likely_relevant | download_xml_or_html | Becas China Three Gorges para estudios de Master. |
| 146 | `BOCYL:BOCYL-D-21042026-75-8` | 2026-04-21 | likely_relevant | download_xml_or_html | Becas Santander/Ayuda Economica para estudiantes de grado y master. |

## Selected Evidence Candidates

Select these 10 candidates for a future scoped evidence download:

| candidate_id | official_identifier | recommended first artifact |
| ---: | --- | --- |
| 126 | `BOCYL:BOCYL-D-15052026-91-8` | XML or HTML |
| 128 | `BOCYL:BOCYL-D-14052026-90-7` | XML or HTML |
| 129 | `BOCYL:BOCYL-D-13052026-89-10` | XML or HTML |
| 131 | `BOCYL:BOCYL-D-12052026-88-14` | XML or HTML |
| 134 | `BOCYL:BOCYL-D-11052026-87-8` | XML or HTML |
| 138 | `BOCYL:BOCYL-D-06052026-84-9` | XML or HTML |
| 141 | `BOCYL:BOCYL-D-04052026-82-17` | XML or HTML |
| 142 | `BOCYL:BOCYL-D-04052026-82-39` | XML or HTML |
| 145 | `BOCYL:BOCYL-D-29042026-80-7` | XML or HTML |
| 146 | `BOCYL:BOCYL-D-21042026-75-8` | XML or HTML |

Rationale:

```text
Prefer XML or HTML first because BOCYL already preserves official URL fields and
these formats should be easier to parse and hash than PDF. Use PDF only as a
fallback or for final human-facing evidence if XML/HTML is incomplete.
```

## Noise Observations

Main false-positive families:

- PDI / staff mobility scholarships;
- public employment or tribunal notices that match `discapacidad`;
- education-service notices with `alumnado` but no aid/call;
- awards/prizes that mention students but are not aid/subsidy evidence.

The BOCYL profile is good enough for limited candidate creation, but the next
profile refinement should add explicit exclusions for:

```text
personal docente e investigador
PDI
concurso-oposicion
tribunal calificador
servicios esenciales
premios
seleccion de centros
```

## Status Verification

Post-triage verification:

```text
source_candidates unchanged at 146
BOCYL candidates unchanged at 21
review_status remains human_review_required for all 146 candidates
artifact_download_attempts unchanged at 442
artifact directory unchanged at 30M
DB validation remains valid
```

No writes were intentionally performed during triage.

## Next Recommended Task

```text
TASK-AUTO-BOCYL-007 - BOCYL selected candidate evidence download
```

Guardrails:

- limit scope to the 10 selected candidate IDs in this report;
- download XML or HTML first;
- do not write downstream;
- do not approve or publish;
- create a pre/post artifact count and DB validation report.

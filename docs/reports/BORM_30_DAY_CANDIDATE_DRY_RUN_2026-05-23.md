# BORM 30-Day Candidate Dry-Run

Date: 2026-05-24

Task: `TASK-AUTO-BORM-005`

Scope: metadata-only candidate dry-run over the stored BORM 30-day metadata.

No candidates were created. No artifacts were downloaded. No downstream project was touched.

## Context

BORM metadata window:

```text
2026-04-21 -> 2026-05-20
30 dates
25 success
5 no_publication
0 failed
549 documents_fetched
549 documents_new
0 documents_updated
```

Supplement handling in the source metadata:

```text
2026-05-11 -> 2/2026 SUPLEMENTO -> 1 document
2026-05-15 -> 3/2026 SUPLEMENTO -> 2 documents
```

## VPS State

The VPS was updated from:

```text
1c9381a
```

to:

```text
e793563
```

DB validation before and after the dry-run:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

Pre-run counters:

```text
BORM official_documents=549
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
```

## Dry-Run Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BORM \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile borm-ayudas \
  --dry-run \
  --limit 200
```

## Dry-Run Result

```text
documents_scanned=549
matches_total=255
matches_after_filters=16
documents_matched=16
candidates_created=0
candidates_skipped_existing=0
review_status=human_review_required
write_mode=dry_run
match_rate=2.91%
```

Comparison with current baselines:

| Source/profile | Match rate |
| --- | ---: |
| BOE 6-month refined | 1.73% |
| BOJA refined | 2.40% |
| DOGV refined | 6.83% |
| BOCYL refined | 2.72% |
| BOPV calibrated | 0.82% |
| BORM dry-run | 2.91% |

## Keyword And Source Distribution

Matches by keyword:

```text
ayuda=1
ayudas=5
ayudas al estudio=1
becas=2
convocatoria=6
convocatoria de ayudas=1
convocatoria de subvenciones=1
discapacidad=1
empleo=1
estudiantes=4
familias=2
formacion=1
joven=2
jovenes=4
libros de texto=1
material escolar=1
subvenciones=2
universidad=8
universidades=8
```

Matches by section:

```text
I. Comunidad Autonoma=11
IV. Administracion Local=5
```

Matches by department/issuer:

```text
Universidad de Murcia / Consejeria de Medio Ambiente, Universidades, Investigacion y Mar Menor=8
Cartagena=2
Alguazas=1
Fortuna=1
Molina de Segura=1
Consejeria de Empresa, Empleo y Economia Social - SEF=1
Consejeria de Politica Social, Familias e Igualdad=1
IMAS=1
```

Filtering:

```text
excluded_by_section=0
excluded_by_department=0
excluded_by_keyword_rules=239
```

## Sample Matches

Likely relevant or worth evidence later:

| Official identifier | Date | Signal | Notes |
| --- | --- | --- | --- |
| `BORM:A-130526-2111` | 2026-05-13 | ayudas, libros de texto, material escolar | Local school-material aid. Strong fit for `EduAyudas` and possibly `la-ayuda`. |
| `BORM:A-080526-2009` | 2026-05-08 | ayudas, estudiantes, universidad | Erasmus+ practices aid for students. Strong education/student signal. |
| `BORM:A-080526-2010` | 2026-05-08 | becas, ayudas al estudio, estudiantes | Santander study-aid call for university students. Strong signal. |
| `BORM:A-080526-2011` | 2026-05-08 | ayudas, estudiantes, universidad | Aid for students in a university master's program. Strong signal. |
| `BORM:A-080526-2012` | 2026-05-08 | estudiantes, universidad | Campus Rural practices for university students. Likely relevant but evidence should confirm economic aid. |
| `BORM:A-230426-1782` | 2026-04-23 | subvenciones, discapacidad, empleo | Employment/disability integration grant. Needs evidence to confirm beneficiary and downstream fit. |
| `BORM:A-210426-1745` | 2026-04-21 | becas, jovenes | Cartagena youth compensation grants. Strong signal. |
| `BORM:A-210426-1746` | 2026-04-21 | ayudas, jovenes | Youth international mobility aid. Strong signal. |

Likely noise or needs calibration:

| Official identifier | Date | Signal | Noise observation |
| --- | --- | --- | --- |
| `BORM:A-140526-2136` | 2026-05-14 | familias | Dental-health collaboration agreement; not a direct aid call from metadata. |
| `BORM:A-110526-2055` | 2026-05-11 | subvenciones, familias, jovenes | Third-sector entity grants for employability programs; may be indirect/entity funding. |
| `BORM:A-080526-2023` | 2026-05-08 | joven, convocatoria | Artistic youth contest, likely not aid/subsidy. |
| `BORM:A-070526-1989` | 2026-05-07 | universidad | Profesorado Ayudante Doctor hiring competition; should be excluded. |
| `BORM:A-040526-1929` | 2026-05-04 | universidad | Profesorado Ayudante Doctor hiring competition; should be excluded. |
| `BORM:A-040526-1930` | 2026-05-04 | universidad | Modification of hiring competition; should be excluded. |
| `BORM:A-290426-1880` | 2026-04-29 | jovenes | Job pool for youth labor counsellors; employment/procedure noise. |
| `BORM:A-280426-1858` | 2026-04-28 | universidad | Modification of hiring competition; should be excluded. |

## Noise Observations

The overall match rate is reasonable, but the current `borm-ayudas` profile needs light calibration before candidate creation:

- `universidad/universidades` alone overmatches university staff hiring notices.
- `joven/jovenes` alone overmatches youth contests and employment pools.
- Entity/project grants appear in the results and should be downranked unless the title clearly indicates direct citizen/student/family benefit.
- Strong student/education aid signals are present and should be preserved.

The profile is not dangerously broad like the first generic BOCYL run, but it is not ready for candidate creation without a small refinement pass.

## Safety Verification

Post dry-run:

```text
source_candidates=150
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
DB validation=status=valid schema_version=8
MCP privacy=no matching official/mcp/python/uvicorn/fastmcp listeners
```

No writes were observed:

```text
candidates_created=0
artifact_download_attempts unchanged
artifacts unchanged
downstream writes=0
```

## Recommendation

Do not create BORM candidates yet.

Recommended next task:

```text
TASK-AUTO-BORM-005B — BORM candidate profile calibration
```

Target:

- exclude university hiring competitions;
- exclude youth contests and employment-pool notices;
- preserve direct student/family/material-school/youth mobility aid signals;
- rerun dry-run and aim for a first-pass range around `8-12` matches after filters.

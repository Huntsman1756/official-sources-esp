# BOJA 30-Day Candidate Dry-Run - 2026-05-20

## Summary

TASK-AUTO-004 ran a metadata-only candidate dry-run over the stored BOJA 30-day metadata window.

The run did not create candidates, download artifacts, call BOJA, write downstream projects, approve, publish, or expose MCP.

The existing BOE `la-ayuda` profile produces too much noise on BOJA metadata. A BOJA-specific profile is needed before creating real BOJA source candidates.

## Deployed State

VPS application path:

```text
/opt/official-sources/app
```

Deployed commit after fast-forward pull:

```text
7e84235
```

This includes the source-aware candidate dry-run enhancement:

```text
feat: add source-aware candidate dry-run
```

Database status before dry-run:

```text
current_version=8
latest_version=8
status=valid
```

## Source-Aware Dry-Run Support

Before this dry-run, `find-boe-candidates` did not support source filtering and scanned all stored official documents by date. TASK-AUTO-004 added a minimal safe enhancement:

```bash
official-sources find-boe-candidates --source BOJA ...
```

Behavior:

- `--source` accepts `BOE` or `BOJA`;
- default remains `BOE`, preserving existing BOE behavior;
- dry-run remains non-writing;
- write mode remains explicit;
- tests prove BOJA dry-run does not create candidates and BOE default behavior does not scan BOJA documents.

## BOJA Coverage Before Dry-Run

Stored BOJA metadata window:

```text
2026-04-21 to 2026-05-20
```

Coverage:

```text
BOJA official_documents=1500
current latest status: success=21, no_publication=9, failed=0
historical BOJA runs: success=21, no_publication=9, failed=1
source_candidates=75
artifact_download_attempts=392
artifact directory size=24M
```

The historical failed BOJA run is the old `2026-04-25` run from before BOJA HTTP 400 no-publication handling was hardened. The current latest status for that date is `no_publication`.

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --source BOJA \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 200
```

This command used stored BOJA metadata only.

## Dry-Run Metrics

```text
documents_scanned=1500
matches_total=376
matches_after_filters=217
documents_matched=217
candidates_created=0
candidates_skipped_existing=0
write_mode=dry_run
sample_count=200
excluded_by_section=0
excluded_by_department=0
excluded_by_keyword_rules=159
```

Match rates:

```text
raw_match_rate=376/1500 = 25.07%
filtered_match_rate=217/1500 = 14.47%
```

Comparison:

| source/window | documents scanned | matches after filters | match rate |
| --- | ---: | ---: | ---: |
| BOE 30-day refined baseline | 3896 | 73 | 1.87% |
| BOE 6-month refined baseline | 21513 | 372 | 1.73% |
| BOJA 30-day using BOE `la-ayuda` profile | 1500 | 217 | 14.47% |

BOJA match rate is about 7.7x the BOE 30-day baseline and about 8.4x the BOE 6-month baseline.

## Matches By Keyword

| keyword | matches |
| --- | ---: |
| subvenciones | 73 |
| vivienda | 71 |
| bases reguladoras | 50 |
| ayudas | 43 |
| convocatoria | 38 |
| ayuda | 13 |
| discapacidad | 10 |
| becas | 9 |
| beca | 9 |
| alquiler | 8 |
| estudiantes | 5 |
| convocatoria de ayudas | 2 |
| convocatoria de subvenciones | 2 |
| bono | 1 |
| bono social | 1 |

## Matches By Section

| section | matches |
| --- | ---: |
| `5._Anuncios` | 92 |
| `1._Disposiciones_generales` | 70 |
| `3._Otras_disposiciones` | 33 |
| `2._Autoridades_y_personal` | 22 |

## Top Departments

| department | matches |
| --- | ---: |
| Consejeria de Fomento, Articulacion del Territorio y Vivienda | 70 |
| Universidades | 26 |
| Consejeria de Empleo, Empresa y Trabajo Autonomo | 23 |
| Consejeria de Inclusion Social, Juventud, Familias e Igualdad | 14 |
| Consejeria de Sanidad, Presidencia y Emergencias | 12 |
| Consejeria de Agricultura, Pesca, Agua y Desarrollo Rural | 11 |
| Consejeria de Justicia, Administracion Local y Funcion Publica | 10 |
| Consejeria de Cultura y Deporte | 10 |
| Ayuntamientos | 9 |
| Consejeria de Industria, Energia y Minas | 9 |
| Consejeria de Turismo y Andalucia Exterior | 8 |
| Consejeria de Universidad, Investigacion e Innovacion | 6 |
| Consejeria de Desarrollo Educativo y Formacion Profesional | 3 |

## Sample Observations

Likely relevant or high-value unclear examples:

| external_id | date | department | keywords | observation |
| --- | --- | --- | --- | --- |
| `BOJA:disposition.2026.95.6` | 2026-05-20 | Universidades | becas, estudiantes | Scholarship/student wording; likely relevant for downstream evidence review. |
| `BOJA:disposition.2026.94.5` | 2026-05-19 | Universidades | ayudas, estudiantes | Student aid wording; likely relevant. |
| `BOJA:disposition.2026.93.28` | 2026-05-18 | Universidades | becas, convocatoria | Likely relevant or unclear pending evidence. |
| `BOJA:disposition.2026.90.5` | 2026-05-13 | Universidades | becas, ayuda, estudiantes | Likely relevant for education/student aid review. |

Noise or broad-scope examples:

| category | observed pattern |
| --- | --- |
| Housing/vivienda | 70 matches from the housing department; most are not education-specific and dominate the BOJA dry-run. |
| Institutional grants | Ayuntamientos and public-entity notices often match `bases reguladoras`, `convocatoria`, or `ayuda`. |
| Sector-specific subsidies | Agriculture, industry, tourism, culture, and employment departments generate many subsidy hits outside EduAyudas/la-ayuda scope. |
| Generic notices | Section `5._Anuncios` produces many matches that need different filtering from BOE `V-B`. |
| Employment/training | Some employment/training notices may be useful, but the current profile cannot separate citizen training grants from institutional programs. |

## Quality Decision

Do not create BOJA candidates from this dry-run.

The BOE `la-ayuda` profile is not suitable for BOJA candidate creation without refinement. It over-matches because BOJA has many autonomous subsidy, housing, municipal, and institutional notices that share aid vocabulary.

Recommended decision:

```text
needs_boja_specific_profile
```

## Post-Run Safety Checks

After dry-run:

```text
source_candidates=75
artifact_download_attempts=392
artifact directory size=24M
DB validation=status=valid
MCP listener check=no matching public listener observed
```

No DB candidate write occurred.

## Validation

Code validation for source-aware dry-run support:

```text
focused tests: 3 passed
full tests: 233 passed
ruff check: OK
ruff format --check: OK
```

## Known Limitations

- The command name remains `find-boe-candidates`, although it now supports `--source BOJA`.
- The `la-ayuda` profile is BOE-oriented and overmatches BOJA.
- No BOJA-specific profile exists yet.
- No BOJA candidates were created.
- No BOJA artifact downloads exist yet.
- No BOJA downstream export/import exists yet.

## Recommendation

Recommended next task:

```text
TASK-AUTO-004B - BOJA-specific profile refinement
```

Scope:

- create or refine a BOJA-specific dry-run profile;
- reduce housing, municipal, institutional, and sector-specific subsidy noise;
- keep dry-run only;
- no candidates;
- no PDFs;
- no downstream.

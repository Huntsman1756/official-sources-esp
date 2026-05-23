# BOCYL Candidate Profile Refinement - 2026-05-21

## Scope

This report records the BOCYL-specific candidate profile refinement and a
metadata-only VPS dry-run over the stored BOCYL 30-day window.

Rules applied:

- no candidates were created;
- `--write` was not used;
- no PDF/XML/HTML artifacts were downloaded;
- no BOCYL backfill was run;
- no EduAyudas work was performed;
- no `la-ayuda` work was performed;
- no downstream writes were performed;
- no MCP surface was exposed;
- no approvals or publications were performed.

## Context

Previous dry-run:

```text
docs/reports/BOCYL_30_DAY_CANDIDATE_DRY_RUN_2026-05-21.md
commit=d352fd9
```

Input metadata window:

```text
source_code=BOCYL
date_range=2026-04-21 -> 2026-05-20
BOCYL official_documents=773
```

The previous generic `la-ayuda` dry-run overmatched BOCYL:

| metric | value |
| --- | ---: |
| documents scanned | 773 |
| matches total before filters | 334 |
| matches after filters | 265 |
| match rate after filters | 34.28% |

Main noise source:

```text
vivienda
CONSEJERIA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACION DEL TERRITORIO
environmental / urban planning notices
generic institutional grants
```

## CLI Support Added

`find-source-candidates` now supports BOCYL as a source:

```bash
official-sources find-source-candidates --source BOCYL ...
```

New profile:

```text
bocyl-ayudas
```

The profile keeps BOCYL on the generic candidate finder path instead of relying
on read-only ad hoc scripts.

## Profile Rules

Strong signals include student, family, youth, disability, and direct citizen aid
phrases:

```text
beca
becas
ayudas al estudio
ayudas para alumnado
ayudas para estudiantes
comedor escolar
transporte escolar
libros de texto
material escolar
necesidades educativas
formacion profesional
universidad
alumnado
estudiantes
bono alquiler joven
alquiler joven
familia numerosa
familias numerosas
discapacidad
```

Weak terms are not enough alone:

```text
ayudas
subvenciones
convocatoria
vivienda
empleo
formacion
alquiler
```

BOCYL-specific exclusions:

- `vivienda` in the department name alone does not match;
- environmental and urban-planning notices are excluded unless the title has a
  direct citizen-aid signal;
- `Medio Ambiente`, `Ordenacion del Territorio`, `urbanismo`, `planeamiento`,
  `licencias`, `evaluacion ambiental`, `caza`, `pesca`, and `montes` are treated
  as noise indicators;
- generic municipal, local entity, sector, and company grants are excluded unless
  the title has direct student/family/youth/citizen evidence;
- `familias profesionales` is not treated as a family-benefit signal.

## VPS Dry-Run

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOCYL \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile bocyl-ayudas \
  --dry-run \
  --limit 200
```

The command was run on the VPS against the stored BOCYL metadata only. The code
change was applied temporarily over deployed `d352fd9` for the dry-run; the final
repository commit contains the same implementation and this report.

Result:

| metric | value |
| --- | ---: |
| documents scanned | 773 |
| matches total before filters | 435 |
| matches after filters | 21 |
| documents matched | 21 |
| candidates created | 0 |
| excluded by keyword rules | 414 |
| match rate after filters | 2.72% |

Reduction versus previous BOCYL dry-run:

| metric | value |
| --- | ---: |
| previous matches after filters | 265 |
| new matches after filters | 21 |
| absolute reduction | 244 |
| reduction percentage | 92.08% |

Comparison:

| Source/profile baseline | Match rate |
| --- | ---: |
| BOE 6-month refined | 1.73% |
| BOJA refined | 2.40% |
| DOGV refined | 6.83% |
| BOCYL generic `la-ayuda` | 34.28% |
| BOCYL `bocyl-ayudas` | 2.72% |

## Match Distribution

Keywords after filters:

| keyword | count |
| --- | ---: |
| subvenciones | 15 |
| convocatoria | 14 |
| universidad | 14 |
| becas | 11 |
| estudiantes | 6 |
| ayudas | 6 |
| alumnado | 5 |
| formacion | 3 |
| ayuda | 3 |
| convocatoria de ayudas | 2 |
| ayudas al estudio | 2 |
| discapacidad | 2 |
| bases reguladoras | 1 |
| formacion profesional | 1 |
| universidades | 1 |

Excluded by BOCYL profile reason:

| reason | count |
| --- | ---: |
| `bocyl_weak_only` | 338 |
| `bocyl_no_direct_signal` | 65 |
| `bocyl_institutional_or_sector_noise` | 11 |

## Sample Matches

Representative kept matches:

| date | official identifier | signal | title |
| --- | --- | --- | --- |
| 2026-05-15 | `BOCYL:BOCYL-D-15052026-91-8` | `becas`, `estudiantes`, `universidad` | Extracto de convocatoria de 30 becas para estudiantes de la Universidad de Salamanca, Programa Campus Rural. |
| 2026-05-14 | `BOCYL:BOCYL-D-14052026-90-7` | `ayudas`, `alumnado`, `formacion profesional` | Modificacion de bases reguladoras para ayudas complementarias al alumnado de FP beneficiario de Erasmus+. |
| 2026-05-13 | `BOCYL:BOCYL-D-13052026-89-10` | `becas`, `ayudas`, `estudiantes`, `universidad` | Becas Santander Ayuda Economica para estudiantes de grado y master de la Universidad de Valladolid. |
| 2026-05-11 | `BOCYL:BOCYL-D-11052026-87-10` | `ayudas al estudio`, `alumnado` | Resolucion de ayudas al estudio para alumnado de ensenanzas artisticas superiores. |

## Sample Exclusions

Representative filtered noise:

| reason | official identifier | signal | title |
| --- | --- | --- | --- |
| `bocyl_weak_only` | `BOCYL:BOCYL-D-20052026-94-13` | `vivienda` | Informe ambiental estrategico de una modificacion puntual de normas urbanisticas. |
| `bocyl_weak_only` | `BOCYL:BOCYL-D-20052026-94-16` | `vivienda` | Impacto ambiental de una planta solar fotovoltaica. |
| `bocyl_weak_only` | `BOCYL:BOCYL-D-20052026-94-19` | `vivienda` | Impacto ambiental de una modificacion de autorizacion ambiental integrada. |
| `bocyl_institutional_or_sector_noise` | sample group | `subvenciones` | Grants or notices tied to local entities, sectors, companies, or institutional recipients without direct citizen/student/family evidence. |

## Safety Checks

VPS checks after the dry-run:

| check | result |
| --- | --- |
| DB validation | `valid` |
| BOCYL official_documents | 773 |
| source_candidates | 125 |
| artifact_download_attempts | 442 |
| artifact directory size | 30M |
| MCP/privacy listener check | no `official`, `mcp`, `python`, `uvicorn`, or `fastmcp` listener found |

No write was observed:

```text
candidates_created=0
source_candidates unchanged at 125
artifact_download_attempts unchanged at 442
artifact directory unchanged at 30M
```

## Tests

Added coverage for:

- `find-source-candidates --source BOCYL`;
- `bocyl-ayudas` profile selection;
- BOCYL dry-run without writes;
- `vivienda` in the department name alone not matching;
- environmental and urban-planning terms filtered;
- generic `subvenciones` alone treated as weak;
- `ayudas al estudio` matching;
- `bono alquiler joven` matching;
- `familias profesionales` not treated as a family-benefit signal;
- existing BOE/BOJA/DOGV candidate command behavior.

## Limitations

The refined profile is intentionally conservative. It may miss some relevant
direct citizen aid notices that do not use student, youth, family, disability, or
housing-benefit language in the title.

Some kept university matches may still require human review, especially Erasmus
or university-program notices aimed at staff rather than students. This is
acceptable for limited candidate creation because candidates remain
`human_review_required`.

The profile does not classify whether an aid notice is open, resolved, awarded,
or merely modifies bases. That decision remains for later evidence review or a
future scoring refinement.

## Recommendation

BOCYL candidates can proceed to a limited creation task.

Recommended next task:

```text
TASK-AUTO-BOCYL-005 - Create limited BOCYL candidates
```

Suggested guardrails:

- use `--profile bocyl-ayudas`;
- keep a low limit, for example 25;
- create candidates only from stored metadata;
- do not download artifacts;
- do not write downstream;
- keep all candidates in human-review status.

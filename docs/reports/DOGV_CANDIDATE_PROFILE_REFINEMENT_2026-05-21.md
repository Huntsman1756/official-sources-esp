# DOGV Candidate Profile Refinement - 2026-05-21

## Summary

TASK-AUTO-DOGV-004B added a DOGV-specific candidate profile named `dogv-ayudas`.

The profile is deterministic and source-specific. It is designed for stored DOGV metadata and reduces
the heavy over-matching observed with the generic `la-ayuda` profile before any real DOGV candidate
creation.

This task was dry-run only. No `--write` mode was used. No DOGV candidates were created. No PDFs,
XML, HTML, or other artifacts were downloaded. No DOGV backfill was run. No downstream projects were
touched. No MCP exposure was changed.

## Baseline

Previous DOGV dry-run using the generic `la-ayuda` profile:

```text
source=DOGV
date_from=2026-04-21
date_to=2026-05-20
profile=la-ayuda
documents_scanned=1113
matches_total=420
matches_after_filters=286
filtered_match_rate=25.70%
candidates_created=0
```

The generic profile was too broad for DOGV metadata. The dominant noise came from public employment
notices, local/entity-only aid, sector/company subsidies, concessions/results, and broad terms such
as `ayudas`, `subvenciones`, `vivienda`, `empleo`, and `formacion`.

## Profile Added

New profile:

```text
dogv-ayudas
```

The profile keeps broad aid terms visible for diagnostic accounting, but does not let generic
`ayudas`, `subvenciones`, `convocatoria`, `vivienda`, `empleo`, or `formacion` pass on their own.

Strong signals include student, scholarship, school transport/material/meal, direct family/young
person, disability, and housing-plus-youth/rent contexts. DOGV-specific exclusion rules downrank or
exclude likely noise:

```text
oposiciones
bolsas de empleo
nombramientos
listas provisionales / definitivas
tribunales
concesiones / resultados
entidades locales / ayuntamientos
empresas and sector-only subsidies
sector agrario / vitivinicola
industria / energia / infraestructuras
contratacion / licitacion
```

The profile does not modify BOE or BOJA behavior.

## Command Executed

The refined dry-run was executed on the VPS after deploying commit
`55170eed0002b5569a86aa1e25c4ace147f2cfde`:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source DOGV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile dogv-ayudas \
  --dry-run \
  --limit 200
```

The command used stored DOGV metadata only. It did not call DOGV live endpoints and did not download
artifacts.

## Refined Dry-Run Metrics

```text
documents_scanned=1113
matches_total=705
matches_after_filters=76
documents_matched=76
candidates_created=0
candidates_skipped_existing=0
write_mode=dry_run
write_limit=none
excluded_by_section=0
excluded_by_department=0
excluded_by_keyword_rules=629
sample_count=76
```

Match rates:

```text
raw_match_rate=63.34%
filtered_match_rate=6.83%
```

Reduction versus the generic profile:

```text
old_matches_after_filters=286
new_matches_after_filters=76
reduction=210
reduction_percentage=73.43%
```

The refined profile moved DOGV from `25.70%` to `6.83%`. This is still noisier than the refined BOE
and BOJA baselines, but it is inside the target initial range of 30-80 matches for a controlled first
candidate batch.

## Matches By Keyword

| keyword | matches |
| --- | ---: |
| becas | 74 |
| subvenciones | 74 |
| ayudas | 20 |
| convocatoria | 19 |
| universidad | 17 |
| universidades | 12 |
| beca | 11 |
| formacion | 10 |
| empleo | 9 |
| alumnado | 8 |
| subvencion | 7 |
| estudiantes | 5 |
| ayuda | 4 |
| convocatoria de subvenciones | 3 |
| discapacidad | 2 |
| familias | 2 |
| ayudas para estudiantes | 1 |
| convocatoria de ayudas | 1 |

## Matches By Section

| section | matches |
| --- | ---: |
| `III._ACTOS_ADMINISTRATIVOS_/_B)_SUBVENCIONES_Y_BECAS` | 74 |
| `III._ACTOS_ADMINISTRATIVOS_/_C)_OTROS_ASUNTOS` | 2 |

## Matches By Department

| department | matches |
| --- | ---: |
| Universitat Jaume I de Castello | 17 |
| Conselleria de Educacion, Cultura y Universidades | 12 |
| Universidad de Alicante | 10 |
| Labora Servicio Valenciano de Empleo y Formacion | 7 |
| Universidad Miguel Hernandez de Elche | 7 |
| Vicepresidencia Segunda y Conselleria de Presidencia | 7 |
| Universitat Politecnica de Valencia | 3 |
| Conselleria de Justicia, Transparencia y Participacion | 2 |
| Conselleria de Sanidad | 2 |
| Institut Valencia de Cultura | 2 |
| Institut Valencia de Finances | 2 |
| Other departments | 5 |

## Useful Sample Matches

Representative useful matches kept by `dogv-ayudas`:

| identifier | reason |
| --- | --- |
| `DOGV:DOGV-C-2026-16062` | Becas de ayuda para estudiar master universitario. |
| `DOGV:DOGV-C-2026-16067` | Becas para practicas externas internacionales en master. |
| `DOGV:DOGV-C-2026-15801` | Ayudas de estancia en el extranjero dirigidas a alumnado universitario. |
| `DOGV:DOGV-C-2026-15505` | Ayudas para estudiantes en movilidad internacional. |
| `DOGV:DOGV-C-2026-13949` | Becas para alumnado que finaliza estudios universitarios. |
| `DOGV:DOGV-C-2026-12145` | Becas GV-Talent para excelencia academica. |
| `DOGV:DOGV-C-2026-11490` | Ayudas de movilidad para alumnado. |
| `DOGV:DOGV-C-2026-11442` | Ayudas Erasmus+ para estudiantado. |

## Excluded Noise

The refined rules excluded `629` keyword hits before candidate output. The excluded set included the
targeted noise classes:

```text
oposiciones / empleo publico
bolsas de empleo / nombramientos / tribunales
listas provisionales and definitivas
concesiones / resoluciones de concesion / resultados
ayudas municipales or entity-only
company or sector-only subsidies
sector agrario and vitivinicola aid
procurement and contracting notices
housing without youth/family/student/rent context
generic ayudas/subvenciones without a stronger DOGV signal
```

## Remaining Noise

The 76 remaining matches still include some review noise:

```text
sports and culture entity subsidies
employment aid routed through institutions or special employment centers
subsidized loans / liquidity lines
some procedural or correction notices around otherwise relevant student aid
some university research initiation grants that may be less relevant for la-ayuda
```

The profile is therefore suitable for a small, human-reviewed DOGV candidate batch, not for broad
automatic creation or publication.

## Safety Checks

Pre/post checks on the VPS:

```text
DOGV official_documents in range: 1113 -> 1113
source_candidates: 100 -> 100
artifact_download_attempts: 432 -> 432
artifact_directory_size: 26M -> 26M
db_validation: current_version=8 latest_version=8 status=valid
MCP privacy: no matching official/mcp/python/uvicorn/fastmcp listener reported
```

## Local Validation

```text
git diff --check: OK
pytest -q: 316 passed
ruff check .: OK
ruff format --check .: OK
```

Tests added cover:

```text
DOGV profile exists
BOE/BOJA behavior remains isolated
generic ayudas/subvenciones alone are weak
oposiciones and empleo publico noise is excluded
concesiones/results are excluded
transporte escolar matches
ayudas al estudio matches
vivienda+jovenes/alquiler can match
score reasons are present
dry-run does not write source_candidates
```

## Decision

DOGV no longer blocks on profile over-matching. The next step can create a limited DOGV candidate
batch, but only with a low cap and human review.

Recommended next task:

```text
TASK-AUTO-DOGV-005 - Create limited DOGV candidates
max_candidates=25
source=DOGV
profile=dogv-ayudas
date_from=2026-04-21
date_to=2026-05-20
```

The next task should still avoid artifact downloads, downstream writes, publication, MCP exposure,
and any broad automatic approval.

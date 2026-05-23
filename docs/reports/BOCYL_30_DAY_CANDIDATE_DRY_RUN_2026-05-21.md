# BOCYL 30-Day Candidate Dry-Run - 2026-05-21

## Scope

This report records a metadata-only candidate dry-run over the stored BOCYL
30-day metadata window.

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

Input metadata window:

```text
source_code=BOCYL
date_range=2026-04-21 -> 2026-05-20
BOCYL official_documents=773
BOCYL ingestion_runs=30
```

Previous report:

```text
docs/reports/BOCYL_30_DAY_METADATA_BACKFILL_2026-05-21.md
```

VPS state:

```text
path=/opt/official-sources/app
deployed_commit=b4f8603
db_validate_before=valid
db_validate_after=valid
```

## Command Behavior

The requested generic CLI dry-run command was attempted:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOCYL \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 200
```

It failed before scanning because the CLI source allowlist does not yet include
`BOCYL`:

```text
argument --source: invalid choice: 'BOCYL'
choose from 'BOE', 'BOJA', 'DOGV', 'BOCM', 'BDNS'
```

To keep this task docs-only and write-safe, no code was changed. Instead, a
read-only VPS script reused the same internal `la-ayuda` keyword/filter
functions against stored `BOCYL` documents.

## Dry-Run Result

Summary:

| metric | value |
| --- | ---: |
| documents scanned | 773 |
| matches total before filters | 334 |
| matches after filters | 265 |
| match rate after filters | 34.28% |
| excluded by section | 0 |
| excluded by department | 0 |
| excluded by keyword rules | 69 |

Baseline comparison:

| Source/profile baseline | Match rate |
| --- | ---: |
| BOE 6-month refined | 1.73% |
| BOJA refined | 2.40% |
| DOGV refined | 6.83% |
| BOCYL with generic `la-ayuda` profile | 34.28% |

Conclusion:

```text
BOCYL overmatches heavily with the generic la-ayuda profile.
Do not create real BOCYL candidates yet.
```

## Match Distribution

Top keywords after filters:

| keyword | count |
| --- | ---: |
| vivienda | 173 |
| subvenciones | 84 |
| convocatoria | 32 |
| ayudas | 22 |
| bases reguladoras | 16 |
| ayuda | 16 |
| becas | 11 |
| estudiantes | 7 |
| discapacidad | 6 |
| convocatoria de ayudas | 2 |
| ayudas al estudio | 2 |
| convocatoria de subvenciones | 1 |
| subvención | 1 |

Top sections after filters:

| section | count |
| --- | ---: |
| I. COMUNIDAD DE CASTILLA Y LEÓN | 253 |
| III. ADMINISTRACIÓN LOCAL | 11 |
| V. OTROS ANUNCIOS | 1 |

Top departments after filters:

| department | count |
| --- | ---: |
| CONSEJERÍA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACIÓN DEL TERRITORIO | 166 |
| CONSEJERÍA DE AGRICULTURA, GANADERÍA Y DESARROLLO RURAL | 22 |
| CONSEJERÍA DE INDUSTRIA, COMERCIO Y EMPLEO | 19 |
| CONSEJERÍA DE CULTURA, TURISMO Y DEPORTE | 8 |
| UNIVERSIDAD DE BURGOS | 7 |
| CONSEJERÍA DE LA PRESIDENCIA | 7 |
| UNIVERSIDAD DE LEÓN | 6 |
| UNIVERSIDAD DE SALAMANCA | 6 |
| CONSEJERÍA DE EDUCACIÓN | 4 |
| UNIVERSIDAD DE VALLADOLID | 4 |
| CONSEJERÍA DE ECONOMÍA Y HACIENDA | 4 |
| DIPUTACIÓN PROVINCIAL DE LEÓN | 2 |

Observed title terms:

| term | count |
| --- | ---: |
| ambiental | 120 |
| subvenciones | 34 |
| convocatoria | 32 |
| vivienda | 23 |
| ayudas | 22 |
| universidad | 17 |
| bases reguladoras | 15 |
| becas | 11 |
| urbanismo | 7 |

## Sample Matches

The first sample matches were dominated by `vivienda` hits from the same
department:

```text
2026-05-20 BOCYL:BOCYL-D-20052026-94-13 keyword=vivienda department=CONSEJERÍA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACIÓN DEL TERRITORIO
2026-05-20 BOCYL:BOCYL-D-20052026-94-14 keyword=vivienda department=CONSEJERÍA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACIÓN DEL TERRITORIO
2026-05-20 BOCYL:BOCYL-D-20052026-94-15 keyword=vivienda department=CONSEJERÍA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACIÓN DEL TERRITORIO
2026-05-20 BOCYL:BOCYL-D-20052026-94-16 keyword=vivienda department=CONSEJERÍA DE MEDIO AMBIENTE, VIVIENDA Y ORDENACIÓN DEL TERRITORIO
2026-05-19 BOCYL:BOCYL-D-19052026-93-12 keywords=subvenciones,bases reguladoras
2026-05-19 BOCYL:BOCYL-D-19052026-93-13 keywords=subvenciones,bases reguladoras
```

Sample exclusions were generic `convocatoria` hits removed by the generic
`la-ayuda` weak-keyword rule:

```text
2026-05-20 BOCYL:BOCYL-D-20052026-94-3 reason=keyword_rules keyword=convocatoria
2026-05-20 BOCYL:BOCYL-D-20052026-94-33 reason=keyword_rules keyword=convocatoria
2026-05-19 BOCYL:BOCYL-D-19052026-93-10 reason=keyword_rules keyword=convocatoria
2026-05-18 BOCYL:BOCYL-D-18052026-92-27 reason=keyword_rules keyword=convocatoria
```

## Noise Observations

The generic `la-ayuda` profile is too broad for BOCYL:

- `vivienda` overmatches because BOCYL has many records from the environment,
  housing, and territory-planning department.
- `ambiental` and planning/territory records dominate the matched set even when
  the title is not a direct aid/grant opportunity.
- Generic `subvenciones` and `bases reguladoras` signals are useful but need
  department/type context before real candidate creation.
- University hits may be relevant for scholarships or grants, but generic
  `convocatoria` alone is already filtered and should remain weak.

## Write-Safety Verification

Before:

```text
BOCYL official_documents=773
source_candidates=125
artifact_download_attempts=442
artifact_size=30M
```

After:

```text
BOCYL official_documents=773
source_candidates=125
artifact_download_attempts=442
artifact_size=30M
```

No candidates or artifact attempts were created.

## Database Validation

Before:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

After:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## MCP Privacy Check

Command:

```bash
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener observed
```

## Decision

BOCYL needs a source-specific profile before any real candidate creation.

Recommended next task:

```text
TASK-AUTO-BOCYL-004B - BOCYL-specific profile refinement
```

That task should:

- add `BOCYL` to the generic candidate CLI source allowlist;
- add a `bocyl-ayudas` profile;
- suppress housing/planning/environment noise unless the title has direct grant
  or eligible-person signals;
- keep `convocatoria` weak unless paired with stronger education, scholarship,
  grant, vulnerable-person, youth, housing-benefit, or disability context;
- remain dry-run first, with no candidate writes.

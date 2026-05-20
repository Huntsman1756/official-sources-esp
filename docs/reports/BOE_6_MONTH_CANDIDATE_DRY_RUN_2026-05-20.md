# BOE 6-Month Candidate Dry Run - 2026-05-20

## Scope

This report documents a dry-run BOE candidate prefilter over the cached 6-month BOE summary range.

Target range:

```text
2025-11-20 to 2026-05-20
```

Profile:

```text
la-ayuda
```

This task did not call BOE, did not download XML/HTML/PDF artifacts, did not create source candidates, and did not write to any downstream project.

## Deployment State

- Deployed commit: `8e73b6c`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- Pre-run DB validation: valid

## Pre-Run State

Pre-run database counts:

| Item | Count |
|---|---:|
| `official_documents` | 21,627 |
| `official_documents` in target range | 21,513 |
| `source_candidates` | 25 |
| `artifact_download_attempts` | 366 |
| `document_files` | 21,993 |

Pre-run artifact directory size:

```text
23M
```

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --date-from 2025-11-20 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 200
```

The command exited successfully.

## Dry-Run Result

| Metric | Value |
|---|---:|
| Documents scanned | 21,513 |
| Matches total | 2,041 |
| Matches after filters | 372 |
| Documents matched | 372 |
| Candidates created | 0 |
| Excluded by section | 305 |
| Excluded by department | 0 |
| Excluded by keyword rules | 1,364 |
| Sample count emitted | 200 |

Dry-run write mode:

```text
dry_run
```

Candidate review status that would be used in write mode:

```text
human_review_required
```

## Match Rate

```text
372 / 21513 = 1.73%
```

Comparison with the 30-day refined baseline:

| Range | Documents scanned | Matches total | Matches after filters | Match rate |
|---|---:|---:|---:|---:|
| 30-day refined baseline | 3,896 | 313 | 73 | 1.87% |
| 6-month dry-run | 21,513 | 2,041 | 372 | 1.73% |

The 6-month result scales roughly as expected. The filtered match rate is slightly lower than the 30-day baseline.

## Matches By Keyword

| Keyword | Matches |
|---|---:|
| `ayudas` | 147 |
| `subvenciones` | 119 |
| `convocatoria` | 112 |
| `vivienda` | 47 |
| `becas` | 47 |
| `bases reguladoras` | 25 |
| `convocatoria de ayudas` | 20 |
| `subvencion` | 14 |
| `convocatoria de subvenciones` | 11 |
| `estudiantes` | 11 |
| `transporte` | 5 |
| `ayuda` | 4 |
| `alquiler` | 4 |
| `discapacidad` | 2 |
| `bono` | 2 |
| `bono social` | 2 |
| `becas de caracter general` | 1 |
| `beca` | 1 |

## Matches By Section

All filtered matches were in:

```text
V. Anuncios - B. Otros anuncios oficiales
```

| Section | Matches |
|---|---:|
| `V._Anuncios._-_B._Otros_anuncios_oficiales` | 372 |

## Top Departments

| Department | Matches |
|---|---:|
| `MINISTERIO_DE_CULTURA` | 49 |
| `MINISTERIO_DE_HACIENDA` | 41 |
| `MINISTERIO_DE_CIENCIA_INNOVACION_Y_UNIVERSIDADES` | 34 |
| `MINISTERIO_PARA_LA_TRANSICION_ECOLOGICA_Y_EL_RETO_DEMOGRAFICO` | 34 |
| `MINISTERIO_DE_EDUCACION_FORMACION_PROFESIONAL_Y_DEPORTES` | 27 |
| `UNIVERSIDADES` | 25 |
| `MINISTERIO_DE_TRABAJO_Y_ECONOMIA_SOCIAL` | 21 |
| `COMUNIDAD_AUTONOMA_DE_CATALUNA` | 21 |
| `MINISTERIO_DE_DEFENSA` | 14 |
| `MINISTERIO_DE_AGRICULTURA_PESCA_Y_ALIMENTACION` | 12 |
| `MINISTERIO_DE_TRANSPORTES_Y_MOVILIDAD_SOSTENIBLE` | 11 |
| `MINISTERIO_DE_ASUNTOS_EXTERIORES_UNION_EUROPEA_Y_COOPERACION` | 9 |
| `MINISTERIO_DE_IGUALDAD` | 9 |
| `AGENCIA_ESPANOLA_DE_PROTECCION_DE_DATOS` | 8 |
| `MINISTERIO_PARA_LA_TRANSFORMACION_DIGITAL_Y_DE_LA_FUNCION_PUBLICA` | 7 |
| `MINISTERIO_DE_VIVIENDA_Y_AGENDA_URBANA` | 7 |
| `MINISTERIO_DE_ECONOMIA_COMERCIO_Y_EMPRESA` | 6 |
| `MINISTERIO_DEL_INTERIOR` | 6 |
| `MINISTERIO_DE_DERECHOS_SOCIALES_CONSUMO_Y_AGENDA_2030` | 5 |
| `MINISTERIO_DE_LA_PRESIDENCIA_JUSTICIA_Y_RELACIONES_CON_LAS_CORTES` | 4 |

## Score Distribution

| Score | Matches |
|---|---:|
| 2 | 204 |
| 3 | 81 |
| 4 | 38 |
| 6 | 31 |
| 5 | 14 |
| 7 | 3 |
| 8 | 1 |

## Sample Observations

The first 200 dry-run samples were metadata-only BOE title matches. No XML, HTML or PDF evidence was downloaded.

Representative sample identifiers from the emitted dry-run output:

| Identifier | Initial observation |
|---|---|
| `BOE-B-2026-15350` | Known strong EduAyudas fit from the pilot: books/material aid. |
| `BOE-B-2026-14562` | Known strong EduAyudas fit from the pilot: NEAE aid. |
| `BOE-B-2026-15543` | Likely education/training adjacent; needs evidence before downstream use. |
| `BOE-B-2026-16157` | SEPE provincial grant notice; likely unclear without evidence. |
| `BOE-B-2026-16158` | SEPE provincial grant notice; likely unclear without evidence. |
| `BOE-B-2026-16238` | Equality/disability grant notice; likely unclear or project/institutional until reviewed. |
| `BOE-B-2026-16025` | Housing-related notice; likely out of EduAyudas scope unless la-ayuda uses it later. |
| `BOE-B-2026-15551` | Culture/cinema aid notice; likely institutional or sectoral. |

Heuristic metadata-only quality buckets over the 372 filtered matches:

| Bucket | Count |
|---|---:|
| Likely relevant or education-adjacent | 158 |
| Unclear from metadata only | 155 |
| Likely out of scope or institutional | 59 |

These buckets are not operational decisions. They are only a metadata-level quality estimate for planning the next candidate creation task.

## Noise Observations

Known noise sources remain present:

- Generic `convocatoria` and `subvenciones` matches still dominate the volume.
- Housing/vivienda matches are useful for `la-ayuda` later, but mostly outside immediate EduAyudas scope.
- Culture, agriculture, defense and institutional grant notices create sectoral or entity/project subsidy noise.
- University and training-related notices are promising but still require evidence review before downstream use.
- Section V-A procurement was excluded by the refined profile; no filtered matches remained in V-A.

## No-Write Verification

Post dry-run checks:

| Item | Before | After |
|---|---:|---:|
| `source_candidates` | 25 | 25 |
| Artifact directory size | 23M | 23M |

Post-run DB validation:

```text
valid
```

No artifact download command was run.

No candidate write command was run.

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Known Issues

- This was metadata-only candidate discovery. It does not prove legal/product relevance.
- The dry-run did not inspect XML, HTML or PDF evidence.
- The previous summary backfill recorded `2026-05-20` as a non-Sunday `404` failure; this task did not retry or reinterpret that failure.
- The filtered candidate pool is manageable but still too large for direct all-at-once evidence review.
- Noise remains around generic grant, housing, culture and institutional notices.

## Recommendation

Recommended next task:

```text
TASK-005C - Create limited 6-month BOE candidates
```

Use a strict cap, for example:

```text
max_candidates=50
```

The next write task should create only a limited candidate batch with `review_status=human_review_required`, then run evidence selection/download only after that batch is reviewed. Do not create all 372 filtered matches at once.

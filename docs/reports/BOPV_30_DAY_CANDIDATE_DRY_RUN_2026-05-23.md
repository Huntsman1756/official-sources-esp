# BOPV/EHAA 30-Day Candidate Dry-Run - 2026-05-23

## Scope

- VPS: `mcpspain-official-sources-vps` (`root@157.90.22.40`)
- App path: `/opt/official-sources/app`
- Database: `/opt/official-sources/data/official_sources.sqlite`
- Deployed commit before sync: `c10ff19`
- Deployed commit after `git pull --ff-only origin main`: `89a7da7`
- Date range: `2026-04-21` through `2026-05-20`
- Source: `BOPV`
- Profile: `la-ayuda`
- Mode: dry-run / read-only only

No candidates were created. `--write` was not used. No artifacts were downloaded. No downstream
project was touched. No other source operations were run.

## Pre-Run State

Remote preflight:

```text
remote_git_status=clean
db_validation_before=valid
schema_version=8
BOPV_source_id=519
BOPV_official_documents=489
source_candidates_before=146
artifact_download_attempts_before=482
artifact_directory_size_before=28857411 bytes
artifact_directory_human_before=30M
MCP_privacy_before=no matching official/mcp/python/uvicorn/fastmcp listeners
```

The VPS app was initially behind `origin/main`:

```text
local_head=c10ff19
origin_main=89a7da7
behind_by=8
```

It was fast-forwarded to current `main` before retrying the requested command.

## Requested Command

The exact requested command was executed after syncing the VPS app to current `main`:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOPV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 200
```

It failed before scanning because current `main` does not include `BOPV` in the
`find-source-candidates --source` allowlist:

```text
argument --source: invalid choice: 'BOPV'
choose from 'BOE', 'BOJA', 'DOGV', 'BOCM', 'BOCYL', 'BDNS'
```

No DB writes or artifact downloads occurred during this failed CLI invocation.

## Read-Only Equivalent Scan

To preserve write safety and still measure candidate pressure, a read-only VPS Python script reused
the deployed candidate matching functions against stored `BOPV` documents:

- `OfficialSourcesRepository.search_documents(...)`
- `_candidate_keywords(...)`
- `_candidate_filters(...)`
- `_candidate_keyword_matches(...)`
- `_candidate_exclusion_reason(...)`
- `_candidate_evidence_metadata(...)`

The SQLite connection used `mode=ro`. This did not create candidates or artifact attempts.

## Dry-Run Metrics

| Metric | Value |
| --- | ---: |
| Documents scanned | 489 |
| Matches total before filters | 117 |
| Matches after filters | 81 |
| Documents matched after filters | 81 |
| Candidates created | 0 |
| Excluded by section | 0 |
| Excluded by department | 0 |
| Excluded by keyword rules | 36 |
| Sample count | 81 |
| Raw match rate | 23.93% |
| Filtered match rate | 16.56% |

Conclusion:

```text
BOPV overmatches with the generic la-ayuda profile.
Do not create real BOPV candidates yet.
BOPV needs CLI source support and a source-specific profile before write-mode candidate creation.
```

## Keyword Signals

Top keyword counts after filters:

| Keyword | Count |
| --- | ---: |
| ayudas | 43 |
| subvenciones | 28 |
| convocatoria | 20 |
| vivienda | 18 |
| bases reguladoras | 15 |
| transporte | 6 |
| convocatoria de subvenciones | 4 |
| becas | 3 |
| alquiler | 3 |
| ayuda | 2 |
| convocatoria de ayudas | 2 |
| bono | 1 |
| bono social | 1 |
| discapacidad | 1 |

## Section and Department Distribution

Sections after filters:

| Section | Count |
| --- | ---: |
| OTRAS_DISPOSICIONES | 57 |
| ANUNCIOS | 19 |
| AUTORIDADES_Y_PERSONAL | 4 |
| DISPOSICIONES_GENERALES | 1 |

Top departments after filters:

| Department | Count |
| --- | ---: |
| LANBIDE-SERVICIO_PUBLICO_VASCO_DE_EMPLEO | 13 |
| DEPARTAMENTO_DE_VIVIENDA_Y_AGENDA_URBANA | 12 |
| DEPARTAMENTO_DE_CULTURA_Y_POLITICA_LINGUISTICA | 12 |
| DEPARTAMENTO_DE_BIENESTAR_JUVENTUD_Y_RETO_DEMOGRAFICO | 11 |
| DEPARTAMENTO_DE_ALIMENTACION_DESARROLLO_RURAL_AGRICULTURA_Y_PESCA | 6 |
| DEPARTAMENTO_DE_EDUCACION | 5 |
| DEPARTAMENTO_DE_MOVILIDAD_SOSTENIBLE | 5 |
| ENTE_VASCO_DE_LA_ENERGIA | 4 |
| DEPARTAMENTO_DE_CIENCIA_UNIVERSIDADES_E_INNOVACION | 4 |
| DEPARTAMENTO_DE_SALUD | 2 |
| DEPARTAMENTO_DE_INDUSTRIA_TRANSICION_ENERGETICA_Y_SOSTENIBILIDAD | 2 |

## Noise Assessment

Heuristic multi-label scan over the 81 filtered matches:

| Category | Count |
| --- | ---: |
| false_positive_hr | 50 |
| company_sectoral | 25 |
| employment_training | 22 |
| housing | 20 |
| concession_or_award | 18 |
| family_social | 14 |
| education_student | 8 |

Observed useful signals:

- Housing and rent-related signals are present, including `vivienda`, `alquiler`, and related
  BOPV housing programs.
- Education/student signals are present but small in this 30-day window.
- Some Lanbide and employment/training records may be useful, but metadata alone is too broad.
- Social, youth, disability, and family signals appear in the filtered set.

Observed noise:

- Generic `convocatoria` and broad `ayudas`/`subvenciones` terms produce many procedural or
  institution-facing records.
- `AUTORIDADES_Y_PERSONAL` and announcement-style records create public-employment and staffing
  false positives.
- Company, sectoral, energy, culture, agriculture, and agency grant programs are mixed with direct
  citizen aid signals.
- Some hits are concessions, award resolutions, or procedural notices rather than open aid calls.

## Representative Samples

Useful or potentially useful samples:

| Date | Identifier | Keywords | Department | Observation |
| --- | --- | --- | --- | --- |
| 2026-05-20 | `BOPV:BOPV-2026-05-2602124a` | vivienda | Departamento de Vivienda y Agenda Urbana | Housing signal, needs profile rules to distinguish notices from direct aid. |
| 2026-05-15 | `BOPV:BOPV-2026-05-2602040a` | vivienda | Departamento de Vivienda y Agenda Urbana | Housing department signal. |
| 2026-05-11 | `BOPV:BOPV-2026-05-2601956a` | becas, ayudas, convocatoria | Departamento de Educacion | Education/student-aid signal. |
| 2026-05-19 | `BOPV:BOPV-2026-05-2602094a` | ayuda | Departamento de Bienestar, Juventud y Reto Demografico | Social/youth-oriented department signal. |
| 2026-05-18 | `BOPV:BOPV-2026-05-2602070a` | ayudas, bases reguladoras, convocatoria | Ente Vasco de la Energia | Real aid syntax, likely sectoral unless profile narrows it. |

Representative excluded noise:

| Date | Identifier | Keywords | Reason |
| --- | --- | --- | --- |
| 2026-05-20 | `BOPV:BOPV-2026-05-2602112a` | convocatoria | generic weak-keyword rule |
| 2026-05-19 | `BOPV:BOPV-2026-05-2602084a` | convocatoria | staffing/provision notice pattern |
| 2026-05-11 | `BOPV:BOPV-2026-05-2601939a` | convocatoria | staffing/provision notice pattern |
| 2026-05-11 | `BOPV:BOPV-2026-05-2601937a` | transporte | weak transport-only match |

## Write-Safety Verification

Post-run checks:

```text
db_validation_after=valid
schema_version=8
BOPV_official_documents_after=489
source_candidates_after=146
artifact_download_attempts_after=482
artifact_directory_size_after=28857411 bytes
MCP_privacy_after=no matching official/mcp/python/uvicorn/fastmcp listeners
```

Before/after:

| Metric | Before | After | Changed |
| --- | ---: | ---: | --- |
| BOPV official_documents | 489 | 489 | No |
| source_candidates | 146 | 146 | No |
| artifact_download_attempts | 482 | 482 | No |
| Artifact directory size | 28,857,411 bytes | 28,857,411 bytes | No |

## Limitations

- The exact CLI command cannot complete until `find-source-candidates --source` supports `BOPV`.
- The read-only equivalent scan is metadata/title-only and should not be treated as classification.
- The heuristic category counts are rough profile-pressure indicators, not evidence review labels.
- No artifact body, PDF, XML, or HTML evidence was downloaded or inspected.

## Next Recommended Task

Implement BOPV support in the candidate CLI allowlist plus a `bopv-ayudas` profile, then rerun the
same 30-day command as a true CLI dry-run before any candidate write task.

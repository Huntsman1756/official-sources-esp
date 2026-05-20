# BOJA Candidate Profile Refinement - 2026-05-20

## Summary

TASK-AUTO-004B added a BOJA-specific candidate profile named `boja-ayudas`.

The profile is separate from the BOE `la-ayuda` profile. It is designed for stored BOJA metadata and keeps the candidate search deterministic, explainable, and dry-run safe.

No candidates were created. No PDFs, XML, or HTML artifacts were downloaded. No downstream projects were touched.

## Baseline

Previous BOJA dry-run using the BOE `la-ayuda` profile:

```text
source=BOJA
date_from=2026-04-21
date_to=2026-05-20
profile=la-ayuda
documents_scanned=1500
matches_total=376
matches_after_filters=217
filtered_match_rate=14.47%
```

This was too broad for BOJA metadata. The dominant noise came from housing, institutional subsidies, municipal/entity grants, sector-specific subsidies, generic announcements, and broad `subvenciones` / `ayudas` vocabulary.

## Profile Added

New profile:

```text
boja-ayudas
```

The profile keeps generic aid terms visible for exclusion accounting, but only allows candidates through when there is stronger evidence such as student/scholarship wording, disability support, school material/transport/meal wording, young-rent context, or other explicit education/citizen-aid signals.

Broad terms such as `ayudas`, `subvenciones`, `bases reguladoras`, `convocatoria`, `vivienda`, and `alquiler` are treated as weak unless the document also has a stronger BOJA-specific signal.

The profile intentionally does not reuse broad BOJA department terms like `universidad`, `educacion`, `formacion profesional`, or `familias` as direct candidate keywords because those terms over-match metadata and department names.

## Command Executed

On the VPS, after deploying commit `3123763`:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --source BOJA \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile boja-ayudas \
  --dry-run \
  --limit 200
```

This command used stored BOJA metadata only. It did not call BOJA live endpoints.

## Refined Dry-Run Metrics

```text
documents_scanned=1500
matches_total=372
matches_after_filters=36
documents_matched=36
candidates_created=0
excluded_by_keyword_rules=336
filtered_match_rate=2.40%
```

Reduction:

```text
old_matches_after_filters=217
new_matches_after_filters=36
reduction=181
reduction_percentage=83.41%
```

The filtered match rate moved from `14.47%` to `2.40%`, inside the target range for a first limited BOJA candidate batch.

## Matches By Keyword

| keyword | matches |
| --- | ---: |
| discapacidad | 10 |
| becas | 9 |
| beca | 9 |
| ayudas | 8 |
| convocatoria | 8 |
| ayuda | 7 |
| estudiantes | 5 |
| alumnado | 3 |
| vivienda | 3 |
| alquiler | 3 |
| jovenes | 3 |
| bases reguladoras | 2 |
| subvenciones | 1 |
| convocatoria de subvenciones | 1 |

## Matches By Section

| section | matches |
| --- | ---: |
| `5._Anuncios` | 17 |
| `2._Autoridades_y_personal` | 8 |
| `3._Otras_disposiciones` | 6 |
| `1._Disposiciones_generales` | 5 |

## Matches By Department

| department | matches |
| --- | ---: |
| Consejeria de Empleo, Empresa y Trabajo Autonomo | 11 |
| Universidades | 9 |
| Consejeria de Desarrollo Educativo y Formacion Profesional | 3 |
| Consejeria de Fomento, Articulacion del Territorio y Vivienda | 3 |
| Consejeria de Justicia, Administracion Local y Funcion Publica | 3 |
| Consejeria de Sanidad, Presidencia y Emergencias | 2 |
| Ayuntamientos | 2 |
| Consejeria de Universidad, Investigacion e Innovacion | 1 |
| Consejeria de Inclusion Social, Juventud, Familias e Igualdad | 1 |
| Empresas Publicas y Asimiladas | 1 |

## Sample Likely Matches

| external_id | date | department | matched keywords | observation |
| --- | --- | --- | --- | --- |
| `BOJA:disposition.2026.95.6` | 2026-05-20 | Universidades | becas, estudiantes | Strong scholarship/student signal. |
| `BOJA:disposition.2026.94.5` | 2026-05-19 | Universidades | ayudas, estudiantes | Student aid signal; suitable for evidence review. |
| `BOJA:disposition.2026.93.28` | 2026-05-18 | Universidades | becas, convocatoria | Scholarship/call signal; likely useful. |
| `BOJA:disposition.2026.92.1` | 2026-05-15 | Desarrollo Educativo y Formacion Profesional | convocatoria, alumnado | Education/student wording; likely useful. |
| `BOJA:disposition.2026.92.55` | 2026-05-15 | Fomento, Territorio y Vivienda | ayudas, vivienda, alquiler, jovenes | Young-rent context retained intentionally. |

## Sample Exclusions

The profile excluded 336 metadata matches via keyword rules. Sample patterns:

| pattern | reason |
| --- | --- |
| `subvenciones` without education/citizen context | Generic subsidy noise. |
| `bases reguladoras` without stronger aid-recipient signal | Institutional or sectoral rulemaking. |
| `vivienda` without young/student/alumnado context | Housing noise outside the immediate pilot target. |
| `ayudas` alone in university or institutional metadata | Weak aid term without enough downstream signal. |
| broad housing department notices | BOJA-specific source noise; not enough evidence from metadata alone. |

## Safety Verification

After the dry-run:

```text
source_candidates=75
artifact_download_attempts=392
artifact_directory_size=24M
BOJA official_documents=1500
DB validation=status=valid
MCP listener check=no matching listener observed
```

No candidate writes occurred.

## Tests Added

Tests cover:

- `boja-ayudas` profile exists through the CLI profile choice;
- generic `ayudas` alone does not pass BOJA filters;
- education/student signals pass;
- `transporte escolar` passes while generic transport/subsidy noise does not;
- youth housing/rent context can pass;
- BOE default/source behavior remains covered by existing source-aware dry-run tests.

## Validation

Local validation:

```text
git diff --check: passed
rtk python -m pytest -q: 237 passed
rtk python -m ruff check .: passed
rtk python -m ruff format --check .: passed
```

VPS validation:

```text
db validate: valid
dry-run source_candidates: unchanged at 75
dry-run artifact_download_attempts: unchanged at 392
dry-run artifact directory: unchanged at 24M
MCP privacy check: no matching listener observed
```

## Known Limitations

- The BOJA profile is metadata-only. It does not inspect PDFs or full legal text.
- Remaining matches still need human triage before XML/HTML/PDF evidence decisions.
- Some retained `discapacidad`, employment/training, and public-entity records may still be out of scope.
- The command is still named `find-boe-candidates`; source filtering now supports BOJA, but a future generic alias may improve operator clarity.
- BOJA candidate creation should start with a smaller limit than BOE because BOJA has denser subsidy metadata.

## Recommendation

BOJA candidates can now be created in a limited batch.

Recommended next task:

```text
TASK-AUTO-005 - Create limited BOJA candidates
```

Suggested limit:

```text
max_candidates=25
```

Do not download PDFs, create downstream evidence, or publish anything in that task.

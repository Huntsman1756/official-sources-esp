# DOGV 30-Day Candidate Dry-Run

Date: 2026-05-21

## Summary

TASK-AUTO-DOGV-004 ran a controlled candidate dry-run over the stored DOGV 30-day metadata window.

This was dry-run only. No `--write` mode was used. No source candidates were created. No artifacts
were downloaded. No DOGV backfill was run. No downstream projects were touched. No MCP exposure was
changed.

## Deployed Code

```text
deployed_commit=4423c37
repository=/opt/official-sources/app
database=/opt/official-sources/data/official_sources.sqlite
```

The deployed commit includes the generic source-aware candidate command:

```text
official-sources find-source-candidates
```

## Source and Profile

```text
source=DOGV
profile=la-ayuda
date_from=2026-04-21
date_to=2026-05-20
mode=dry_run
limit=200
```

The run used the existing generic `la-ayuda` profile intentionally. No DOGV-specific profile was
applied.

## Commands

Pre-run state:

```bash
cd /opt/official-sources/app
git status --short
git rev-parse --short HEAD

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
```

Dry-run:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source DOGV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 200
```

Post-run checks:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate

du -sh /opt/official-sources/data/artifacts
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

## Pre-Run State

```text
git_status=clean
deployed_head=4423c37
db_validation=valid
DOGV_documents_in_range=1113
source_candidates_before=100
artifact_download_attempts_before=432
artifact_directory_size_before=26M
```

## Dry-Run Result

```text
documents_scanned=1113
matches_total=420
matches_after_filters=286
documents_matched=286
candidates_created=0
candidates_skipped_existing=0
write_mode=dry_run
write_limit=none
excluded_by_section=0
excluded_by_department=0
excluded_by_keyword_rules=134
sample_count=200
```

Match rates:

```text
raw_match_rate=37.74%
filtered_match_rate=25.70%
```

The filtered rate is far above the previous refined baselines:

| source/profile baseline | result |
| --- | ---: |
| BOE 6-month refined | 372 / 21513 = 1.73% |
| BOJA refined | 36 / 1500 = 2.40% |
| DOGV 30-day `la-ayuda` dry-run | 286 / 1113 = 25.70% |

## Keyword and Section Signals

Top keyword counts from the dry-run output:

```text
subvenciones=219
becas=211
ayudas=81
convocatoria=78
vivienda=44
discapacidad=28
subvencion=24
bases reguladoras=20
beca=12
ayuda=9
estudiantes=7
alquiler=4
convocatoria de ayudas=4
convocatoria de subvenciones=3
bono=1
```

Section distribution after filters:

```text
III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS=209
II. AUTORIDADES Y PERSONAL / A) OFERTAS DE EMPLEO PUBLICO, OPOSICIONES Y CONCURSOS=35
III. ACTOS ADMINISTRATIVOS / C) OTROS ASUNTOS=27
I. DISPOSICIONES GENERALES=5
V. ANUNCIOS / C) OTROS ASUNTOS=4
II. AUTORIDADES Y PERSONAL / B) NOMBRAMIENTOS Y CESES=3
V. ANUNCIOS / A) ORDENACION DEL TERRITORIO Y URBANISMO=2
II. AUTORIDADES Y PERSONAL / C) OTROS ASUNTOS=1
```

Notable department concentrations:

```text
Conselleria de Economia, Hacienda y Administracion Publica=42
Vicepresidencia Primera y Conselleria de Vivienda, Empleo, Juventud e Igualdad=34
Universitat Jaume I de Castello=25
Labora Servicio Valenciano de Empleo y Formacion=22
Conselleria de Educacion, Cultura y Universidades=17
Vicepresidencia Segunda y Conselleria de Presidencia=15
Universidad de Alicante=14
Universitat de Valencia=14
Universidad Miguel Hernandez de Elche=11
```

## Noise Assessment

The generic `la-ayuda` profile overmatches DOGV metadata.

Observed useful signals:

- Real education/student aid is present, especially university grants, study aid, practice grants,
  and scholarship-like calls.
- Social, disability, family, youth, employment, training, and housing signals are present.
- DOGV section `III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS` is a strong coarse filter.

Observed noise:

- Staff selection and public employment notices match through words such as `convocatoria`,
  `vivienda`, `empleo`, or department names.
- Municipal/entity-only accessibility grants match strongly because they contain `ayudas`,
  `subvenciones`, `discapacidad`, and DOGV's `SUBVENCIONES Y BECAS` section, but they are often not
  direct-person downstream candidates.
- Sectoral/company/institutional grants are mixed into the same section and need profile-specific
  downranking.
- `subvenciones` and `becas` dominate the DOGV metadata and are too broad as positive signals by
  themselves.
- Some entries are concessions or award results rather than open calls.

Heuristic category scan over the 286 filtered matches produced the following multi-label counts:

```text
general_subsidies=237
education_student=218
employment_training=103
family_social=78
company_sectoral=52
housing=44
false_positive_hr=41
municipal_entity=27
false_positive_other=2
concession_or_award=2
```

The category scan is intentionally rough and is not a replacement for candidate review. It is useful
only to identify profile pressure.

## Sample Matches

Representative useful matches:

| id | signal | observation |
| --- | --- | --- |
| `DOGV:DOGV-C-2026-16061` | university study aid | Red Alicante Estudios tuition aid. |
| `DOGV:DOGV-C-2026-16062` | university study aid | Aid for a master's study path. |
| `DOGV:DOGV-C-2026-16067` | education/training | International external practice grants. |

Representative noisy matches:

| id | signal | observation |
| --- | --- | --- |
| `DOGV:DOGV-C-2026-12390` | housing/employment department keyword | Arbitration appointment notice, not an aid candidate. |
| `DOGV:DOGV-C-2026-15384` | `convocatoria` plus housing entity | Public selection result, not a grant. |
| `DOGV:DOGV-C-2026-15264` | municipal/disability/accessibility grant | Public-entity municipal aid; likely downrank for `la-ayuda`. |

## DOGV Profile Decision

DOGV needs a source-specific profile before creating real candidates.

Recommended profile refinement:

- Require DOGV section `III. ACTOS ADMINISTRATIVOS / B) SUBVENCIONES Y BECAS` for most positive
  matches, with explicit exceptions for strong social/housing/education signals.
- Exclude or strongly downrank `II. AUTORIDADES Y PERSONAL` and public employment/opposition
  sections.
- Exclude or downrank award/concession/result notices unless the downstream profile explicitly
  accepts them.
- Downrank municipal/entity-only grants for `la-ayuda`; keep them for broader subsidy profiles if
  needed.
- Treat `becas`, `subvenciones`, and `convocatoria` as weak DOGV-only signals unless combined with a
  downstream-specific term.
- Create a `dogv-ayudas` or `dogv-la-ayuda` profile before any write-mode run.

## Post-Run Safety Checks

```text
source_candidates_before=100
source_candidates_after=100
artifact_download_attempts_before=432
artifact_download_attempts_after=432
artifact_directory_size_before=26M
artifact_directory_size_after=26M
db_validation_after=valid
MCP_privacy=no matching official/mcp/python/uvicorn/fastmcp listener observed
```

No candidate or artifact counters changed.

## Conclusion

Do not proceed directly to DOGV candidate creation with the generic `la-ayuda` profile.

The dry-run found real useful DOGV signals, but the filtered match rate of `25.70%` is too high for
safe candidate creation. DOGV should get a source-specific profile refinement task first.

## Next Recommended Task

```text
TASK-AUTO-DOGV-004B - DOGV-specific profile refinement
```

Only after that profile is tested with a lower dry-run rate should the project consider:

```text
TASK-AUTO-DOGV-005 - Create limited DOGV candidates
```

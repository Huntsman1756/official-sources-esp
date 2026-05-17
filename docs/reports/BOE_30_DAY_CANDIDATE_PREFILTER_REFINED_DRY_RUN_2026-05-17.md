# BOE 30-day candidate prefilter refined dry-run - 2026-05-17

## Summary

TASK-004C-FIX4 deployed refined BOE candidate keyword matching and reran a safe dry-run over
the cached 30-day BOE range for `la-ayuda` / `EduAyudas`.

No BOE API calls were made during the dry-run. No XML, HTML, or PDF artifacts were downloaded.
No `source_candidates` rows were created. No downstream project was written to. No candidates
were approved or published. MCP remained private and stopped.

## Environment

- Host: private VPS, public IP redacted.
- Application path: `/opt/official-sources/app`.
- Database path: `/opt/official-sources/data/official_sources.sqlite`.
- Artifact path: `/opt/official-sources/data/artifacts`.
- Cached range: `2026-04-18` through `2026-05-17`.
- Deployed commit: `fbdcf42`.

## Baseline

Previous broad dry-run:

```text
documents_scanned=3896
documents_matched=554
candidates_created=0
artifact_size=22M
source_candidates_before=0
source_candidates_after=0
```

Major false-positive sources in the baseline:

- standalone `convocatoria`;
- standalone `transporte`;
- `bono` matching inside unrelated words such as `carbono`;
- procurement-heavy Section `V-A`.

## Refined Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --date-from 2026-04-18 \
  --date-to 2026-05-17 \
  --profile la-ayuda \
  --dry-run \
  --limit 100
```

The `la-ayuda` profile uses accent/case/whitespace normalization, word-boundary matching,
phrase matching, deterministic scoring, Section `V-A` exclusion, and weak-keyword filtering.

## Refined Result

```text
documents_scanned=3896
matches_total=313
matches_after_filters=73
documents_matched=73
candidates_created=0
write_mode=dry_run
excluded_by_section=38
excluded_by_department=0
excluded_by_keyword_rules=202
sample_count=73
```

Compared with the baseline `554` matches:

```text
usable_matches_reduction=481
usable_matches_reduction_percent=86.8
raw_refined_matches_reduction=241
raw_refined_matches_reduction_percent=43.5
```

`matches_total=313` is the count after refined keyword/profile matching but before section and
weak-keyword exclusions. `matches_after_filters=73` is the usable dry-run output after filters.

## Matches by Keyword

```text
ayuda:1
ayudas:27
bases reguladoras:2
becas:10
convocatoria:21
convocatoria de ayudas:1
convocatoria de subvenciones:5
subvenciones:35
subvención:1
vivienda:5
```

Notable reductions:

- `transporte` no longer appears as a standalone output keyword.
- standalone `convocatoria` remains only when another stronger aid-related term also matched.
- short-term word-boundary matching prevents the known `bono` / `carbono` false positive.

## Matches by Section

```text
V._Anuncios._-_B._Otros_anuncios_oficiales:73
```

Section `V-A` procurement-heavy matches were excluded by the `la-ayuda` profile:

```text
excluded_by_section=38
```

## Matches by Department

```text
MINISTERIO_DE_CULTURA:12
MINISTERIO_DE_TRABAJO_Y_ECONOMÍA_SOCIAL:9
MINISTERIO_DE_DEFENSA:7
MINISTERIO_DE_EDUCACIÓN,_FORMACIÓN_PROFESIONAL_Y_DEPORTES:7
MINISTERIO_DE_ASUNTOS_EXTERIORES,_UNIÓN_EUROPEA_Y_COOPERACIÓN:6
MINISTERIO_DE_IGUALDAD:5
MINISTERIO_PARA_LA_TRANSICIÓN_ECOLÓGICA_Y_EL_RETO_DEMOGRÁFICO:4
COMUNIDAD_AUTÓNOMA_DE_CATALUÑA:3
MINISTERIO_DE_HACIENDA:3
UNIVERSIDADES:3
```

Smaller counts also appeared for Agriculture, Science, Social Rights, Economy, Industry,
Youth and Children, Presidency/Justice, Territorial Policy, Health, and Digital
Transformation.

## Sample Matches

Representative sample rows from the dry-run:

| Identifier | Date | Keywords | Score | Department | Observation |
|---|---|---|---:|---|---|
| BOE-B-2026-15543 | 2026-05-15 | ayudas | 2 | Presidency / Justice | Training grants. |
| BOE-B-2026-15551 | 2026-05-15 | ayudas | 2 | Culture | Film production grants. |
| BOE-B-2026-15552 | 2026-05-15 | ayudas | 2 | Youth and Children | European Solidarity Corps grants. |
| BOE-B-2026-15495 | 2026-05-14 | subvenciones, convocatoria | 3 | Labour | Employment office facility renewal grants. |
| BOE-B-2026-15525 | 2026-05-14 | subvenciones | 2 | Culture | Public library modernization grants. |
| BOE-B-2026-15350 | 2026-05-13 | ayudas | 2 | Education | Textbook and teaching material aid. |
| BOE-B-2026-15228 | 2026-05-12 | subvenciones, convocatoria, convocatoria de subvenciones | 6 | Labour | Employment and training programme grants. |
| BOE-B-2026-14562 | 2026-05-08 | ayudas | 2 | Education | Aid for students with specific educational support needs. |
| BOE-B-2026-13097 | 2026-04-25 | ayudas | 2 | Education | Student participation aid for Spanish theatre festival. |
| BOE-B-2026-12202 | 2026-04-18 | subvenciones | 2 | Culture | Rural reading promotion grants. |

Sample output includes `official_identifier`, `publication_date`, `section`, `department`,
`matched_keywords`, deterministic `score`, `score_reasons`, `official_url`, and title metadata.

## False-positive Observations

Remaining noise:

- `vivienda` still matches some public-information notices that are not citizen-facing aid.
- university title-loss notices can match `becas` or `ayudas` because the office name contains
  those words.
- some grants are real grants but may be irrelevant to `la-ayuda` / `EduAyudas` depending on
  project scope, for example industrial, cultural, or institutional grants.

Reduced noise:

- irrigation-community meeting calls were removed because standalone `convocatoria` is now weak.
- public procurement-heavy Section `V-A` was removed by the profile.
- standalone transport procurement/infrastructure notices were removed.
- `bono` no longer matches inside unrelated words such as `carbono`.

## No-write Verification

```text
source_candidates_before=0
source_candidates_after=0
artifact_size_before=22M
artifact_size_after=22M
database_status_before=valid
database_status_after=valid
```

## MCP Privacy Check

`ss -tulpn` showed no MCP/FastMCP/Python/Uvicorn/official-sources listener and no SQLite
exposure. Public SSH and loopback DNS listeners were present as expected. The public IP is not
recorded in this report.

## Known Limitations

- Matching is still title/metadata-only.
- It does not parse full document content.
- It does not call BOE or download artifacts.
- It does not classify legal, fiscal, eligibility, or product relevance.
- Scores are deterministic matching explanations, not rankings or approval signals.
- Real candidate creation still requires explicit operator approval and should start with a
  small write-mode pilot.

## Recommendation

The refined dry-run is precise enough for a small manually reviewed candidate creation pilot, but
not for automatic approval or publication.

Recommended next step:

```text
TASK-004C-RUN3 - Create a small reviewed BOE candidate pilot
```

Suggested constraints:

- run only against the same cached 30-day range;
- use `--profile la-ayuda`;
- cap candidate creation explicitly;
- backup before write mode;
- inspect created `human_review_required` rows;
- do not download artifacts until candidates are selected for evidence review.

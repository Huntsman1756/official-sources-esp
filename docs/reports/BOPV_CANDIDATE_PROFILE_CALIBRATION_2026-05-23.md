# BOPV Candidate Profile Calibration - 2026-05-23

## Scope

Calibrated the `bopv-ayudas` candidate profile after the first real CLI dry-run showed that the
profile was too restrictive.

This was dry-run only.

No candidates were created. No artifacts were downloaded. No downstream projects were touched.

## Starting Point

Previous real CLI dry-run:

```text
documents_scanned=489
matches_total=177
matches_after_filters=1
match_rate=0.20%
excluded_by_keyword_rules=176
```

Previous broad read-only workaround:

```text
documents_scanned=489
matches_after_filters=81
match_rate=16.56%
```

Conclusion:

```text
la-ayuda overmatched BOPV
bopv-ayudas overcorrected and likely missed real aid calls
```

## False Negatives Found

The calibration review found likely false negatives among excluded high-signal BOPV metadata:

| Candidate pattern | Classification | Reason |
| --- | --- | --- |
| Education orders with `bases reguladoras` + `subvenciones` + `Formacion Profesional` | probably_should_match | Opening call / regulatory bases for training-related grants |
| University/science orders with `bases reguladoras` + `ayudas` | probably_should_match | Opening call / regulatory bases, not a staff or appointment notice |
| Lanbide call with `ayudas` + `discapacidad` | already matched | Kept by the first profile |
| Education/family/vivienda `ANUNCIO` notification rows | correctly_excluded | Procedural notices, not opening calls |
| `relacion de beneficiarios` result rows | correctly_excluded after calibration | Award/result notices, not new candidate calls |

The main technical cause was that BOPV exclusion rules inspected `raw_metadata_json` for noise.
That field can contain neighboring or broad metadata terms such as `oposiciones`, `contratacion`,
or `empresas`, which wrongly excluded otherwise direct title signals.

## Rules Changed

The profile was calibrated as follows:

- added BOPV Basque terms:
  - `beka`, `bekak`;
  - `ikasle`, `ikasleak`;
  - `laguntza`, `laguntzak`;
  - `dirulaguntza`, `dirulaguntzak`;
  - `unibertsitate`;
  - `gazte`, `gazteak`;
- kept generic Basque aid terms weak when alone;
- kept generic Spanish `ayudas`, `subvenciones`, `convocatoria`, `vivienda`, `empleo`,
  `formacion` weak when alone;
- stopped using `raw_metadata_json` for autonomous profile noise exclusion;
- allowed `formacion profesional` when paired with aid context such as `subvenciones`,
  `ayudas`, `becas`, `bases reguladoras`, or Basque grant terms;
- allowed university context when paired with aid context;
- added result/award exclusions for beneficiary-list notices.

The calibration did not loosen generic `ayudas` alone.

## Calibrated Dry-Run

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOPV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile bopv-ayudas \
  --dry-run \
  --limit 200
```

Result:

```text
documents_scanned=489
matches_total=177
matches_after_filters=4
documents_matched=4
candidates_created=0
candidates_skipped_existing=0
excluded_by_section=0
excluded_by_department=0
excluded_by_keyword_rules=173
match_rate=0.82%
```

Reduction versus broad workaround:

```text
81 -> 4
95.06% reduction
```

Increase versus first `bopv-ayudas` profile:

```text
1 -> 4
```

## Accepted Dry-Run Matches

| Official identifier | Date | Signal | Notes |
| --- | --- | --- | --- |
| `BOPV:BOPV-2026-05-2602039a` | 2026-05-15 | `bases reguladoras`, `convocatoria de subvenciones`, `formacion profesional` | Education/FP grant bases |
| `BOPV:BOPV-2026-05-2601909a` | 2026-05-08 | `ayudas`, `bases reguladoras`, `universidades` | Research aid bases/call |
| `BOPV:BOPV-2026-04-2601788a` | 2026-04-30 | `ayudas`, `discapacidad`, `empleo` | Disability/employment stable aid call |
| `BOPV:BOPV-2026-04-2601716a` | 2026-04-24 | `subvenciones`, `bases reguladoras`, `formacion profesional` | Education/FP grant bases |

## Sample Exclusions

| Pattern | Decision |
| --- | --- |
| University rector resolutions in `AUTORIDADES Y PERSONAL` | correctly_excluded |
| Osakidetza and municipal selection/appointment notices | correctly_excluded |
| `ANUNCIO` notification rows for education/family/vivienda proceedings | correctly_excluded |
| Relations of beneficiaries / already awarded aid notices | correctly_excluded |
| Generic `convocatoria`, `ayudas`, `laguntza`, or `vivienda` alone | correctly_excluded |

## Safety Checks

Post-run state:

```text
source_candidates=146
artifact_download_attempts=482
BOPV official_documents=489
artifact_bytes=28857411
DB validation=status=valid schema_version=8
MCP privacy=no official/mcp/python/uvicorn/fastmcp listener output
```

No writes were observed:

```text
candidates_created=0
artifact_download_attempts unchanged
artifact size unchanged
downstream writes=0
```

## Validation

Local validation:

```text
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 418 passed, 1 warning
ruff check: passed
ruff format --check: passed
```

## Decision

Do not create BOPV candidates automatically in this task.

The profile is now conservative but usable: it recovers clear false negatives while keeping the
candidate count low and excluding result/procedural notices. Limited BOPV candidate creation can
be considered next with an explicit low limit of `4`, but the operator should accept that this is
a narrow first pass and may miss additional legitimate aids until more BOPV evidence is reviewed.

## Next Recommended Task

```text
TASK-AUTO-BOPV-005 - Create limited BOPV candidates
```

Recommended guardrails:

```text
--source BOPV
--profile bopv-ayudas
--date-from 2026-04-21
--date-to 2026-05-20
--limit 4
--write
backup before write
no artifacts
no downstream
verify source_candidates increases by at most 4
```

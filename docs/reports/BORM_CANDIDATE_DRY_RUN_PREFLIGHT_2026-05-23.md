# BORM Candidate Dry-Run Preflight - 2026-05-23

## Scope

Task: `TASK-AUTO-BORM-004-PREP`.

This report prepares BORM for a future candidate dry-run readiness decision.

Scope observed:

```text
local inspection only
no VPS connection
no production database write
no source candidates created
no artifact downloads
no downstream writes
no unrelated adapter changes
```

## Sources Inspected

- `src/official_sources/sources/borm/client.py`
- `src/official_sources/sources/borm/parser.py`
- `src/official_sources/sources/borm/ingestion.py`
- `src/official_sources/cli.py`
- `src/official_sources/storage/repository.py`
- `tests/test_borm_adapter.py`
- `tests/test_cli_borm.py`
- `tests/test_cli.py`
- `docs/reports/BORM_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/BORM_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/PREFLIGHT_AND_BOPV_BACKFILL_INTEGRATION_2026-05-23.md`

## Current Readiness

BORM is not ready for a candidate dry-run with the current CLI surface.

The BORM metadata adapter and `ingest-borm-date` command exist, but
`find-source-candidates` does not currently accept `--source BORM`.

Observed CLI help:

```text
--source {BOE,BOJA,DOGV,BOCM,BOCYL,BDNS}
```

Observed attempted command result:

```text
official-sources find-source-candidates: error: argument --source: invalid choice: 'BORM' (choose from BOE, BOJA, DOGV, BOCM, BOCYL, BDNS)
```

This means a BORM candidate dry-run must not be scheduled until the candidate finder source allowlist
and tests explicitly include BORM.

## Recommended Command

Do not run this command yet. It is the intended command shape after BORM is added to
`find-source-candidates` and after a BORM-specific candidate profile is reviewed:

```bash
official-sources find-source-candidates \
  --source BORM \
  --date-from 2026-04-24 \
  --date-to 2026-05-23 \
  --profile borm-ayudas \
  --dry-run \
  --limit 50
```

If `borm-ayudas` is not implemented yet, the only acceptable temporary measurement path is a
conservative custom keyword dry-run, still after `--source BORM` support exists:

```bash
official-sources find-source-candidates \
  --source BORM \
  --date-from 2026-04-24 \
  --date-to 2026-05-23 \
  --keywords "subvencion,subvenciones,ayuda,ayudas,bases reguladoras,convocatoria" \
  --dry-run \
  --limit 50
```

Do not use `--write` for the first BORM candidate operation.

## Candidate Finder Support

`find-source-candidates` is implemented as a generic local metadata scanner. It searches stored
`official_documents` rows by source code and date range, then applies keyword/profile filters.

The storage query is source-aware and could scan BORM documents once the CLI accepts BORM. The current
blocker is the CLI allowlist:

```text
SOURCE_CANDIDATE_SOURCE_CODES = ("BOE", "BOJA", "DOGV", "BOCM", "BOCYL", "BDNS")
```

Focused test coverage currently verifies generic dry-run support for `DOGV`, `BOCM`, and `BDNS`, but
not BORM. A BORM enablement change should add a focused dry-run test proving:

```text
--source BORM is accepted
only BORM documents are scanned
--dry-run creates zero source_candidates
sample output preserves BORM external_id and official URL
```

## Source-Specific Profile Need

BORM likely needs a source-specific profile before the first useful quality measurement.

Reasoning:

- Existing profiles are tuned for BOE-like, BOJA, DOGV, or BOCYL metadata and exclusion patterns.
- BORM stores autonomous-region metadata with BORM-specific sections, departments, announcement
  categories, and official identifiers.
- The generic `la-ayuda` profile is conservative for some sources, but it was not calibrated on BORM
  section/category vocabulary.
- Candidate quality should be measured against BORM's `Sumario`, `Anunciante`, `Administracion`,
  `Seccion`, `Apartado`, `Rango`, and `Categoria` fields before write mode is considered.

Recommended profile name:

```text
borm-ayudas
```

Recommended first-pass behavior:

```text
include direct aid/subsidy signals
preserve broad measurement counters in dry-run
exclude obvious procurement, employment-listing, sanction, correction, and purely administrative noise
avoid department-only matching until BORM sections/categories have been sampled
```

## Current-Index And Historical Range Risks

BORM ingestion currently fetches the official current-year XML index:

```text
https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml
```

The parser filters records where `Fec_Publicacion` starts with the requested date.

This strategy is acceptable for the current May 2026 30-day window if the metadata backfill has been
run and validated first. It is not acceptable as a broad historical or cross-year strategy without
identifying archived annual index resources.

Candidate dry-run risk is lower than ingestion risk only after documents already exist locally. The
dry-run itself should not fetch the current index, download artifacts, or touch downstream outputs.

Risk controls:

```text
candidate dry-run must read only local official_documents
date range must match the validated BORM metadata backfill window
do not infer missing dates from current index at candidate time
do not expand into older years until historical index coverage is documented
```

## Risks

- `--source BORM` is not currently supported by `find-source-candidates`.
- No BORM-specific candidate profile exists.
- Generic subsidy keywords may overmatch BORM administrative announcements.
- Current-year index strategy blocks broad historical or cross-year assumptions.
- BORM raw metadata stores rich nested `raw_document` fields; profile rules should be based on sampled
  real BORM rows, not copied from BOA/DOGC/BOE.
- Candidate dry-run is only meaningful after a BORM metadata backfill has populated local BORM
  documents for the intended range.
- First write mode would still require a separate approval, backup, and post-write evidence review.

## Stop Conditions

Stop before candidate dry-run if any of these are true:

```text
find-source-candidates help does not list BORM
no BORM metadata rows exist for the target range
the intended date range differs from the validated BORM metadata backfill range
db validate is invalid
the command requires --write to produce useful output
the run would download PDF, HTML, XML, or other artifacts
the run would create source_candidates
the run would touch downstream evidence or benefit files
the profile is copied from another source without BORM sample review
matches are dominated by obvious procurement, sanction, personnel, or correction noise
weekday metadata gaps have not been reconciled with ingestion_run status
```

Stop after dry-run if any of these appear:

```text
candidates_created is not 0
source_candidates count changes
artifact_download_attempts count changes
document_files gains PDF, HTML, XML, or non-raw candidate artifacts
sample output lacks BORM external identifiers or official URLs
matches_after_filters is implausibly high and cannot be explained by sampled rows
the sample does not include enough metadata to support human review
```

## BOA/DOGC Comparison

BORM is safer than BOA and DOGC as the next metadata operation among those three, as previously
documented: BORM has a clean local metadata smoke and no pagination cursor risk for the current-year
30-day window.

BORM is not yet safer as the next candidate dry-run operation because the generic candidate command
does not accept BORM today. Once `--source BORM` and a BORM-specific profile exist, BORM should be a
better next candidate-quality measurement target than BOA or DOGC because:

- BORM has a simpler current-year index model than BOA's document-list cap risk.
- BORM avoids DOGC's first-page/pagination and live connectivity concerns.
- BORM metadata includes direct title, department/administration, section, category, and official URL
  fields that are suitable for a metadata-only dry-run.

## Decision

Do not run BORM candidate dry-run yet.

Next local implementation task should add BORM to `find-source-candidates`, add focused tests, and
define or at least explicitly document a `borm-ayudas` profile. After that, the first BORM candidate
operation should be dry-run only, against the validated 30-day metadata range, with zero artifacts and
zero candidate writes.

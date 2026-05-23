# Candidate Source Support for BOPV, BOA, BORM and DOGC - 2026-05-23

## Scope

Added official candidate dry-run support for four autonomous bulletin metadata sources:

- `BOPV`
- `BOA`
- `BORM`
- `DOGC`

This change only enables candidate scanning through `find-source-candidates`. It does not create candidates, download artifacts, run backfills or write downstream.

## CLI Support Added

`find-source-candidates --source` now accepts:

```text
BOPV
BOA
BORM
DOGC
```

Existing supported sources remain unchanged:

```text
BOE
BOJA
DOGV
BOCM
BOCYL
BDNS
```

## Profiles Added

New source-specific profiles:

```text
bopv-ayudas
boa-ayudas
borm-ayudas
dogc-ayudas
```

The first-pass profile strategy is conservative:

- generic `ayudas`, `subvenciones`, `convocatoria`, `vivienda`, `empleo` and `formacion` are not sufficient alone;
- employment/oposiciones, appointment, tribunal and public-staffing notices are excluded;
- procurement, urbanism, environment, sectoral/industry/agriculture/company and local-entity noise is downranked/excluded unless the title has a direct citizen/student/family aid signal;
- direct student/family/youth aid signals are retained;
- DOGC includes a small Catalan keyword seed for future profile refinement.

## Tests Added

Added focused CLI coverage for:

- `find-source-candidates --source BOPV`;
- `find-source-candidates --source BOA`;
- `find-source-candidates --source BORM`;
- `find-source-candidates --source DOGC`;
- each new profile being accepted by argparse;
- weak/generic terms alone being filtered;
- employment/oposiciones noise being filtered;
- student aid phrases matching;
- youth rental aid phrases matching;
- dry-run creating zero `source_candidates`;
- existing BOE/BOJA/DOGV/BOCYL/BDNS behavior remaining covered by the existing CLI suite.

## Validation

Local validation:

```text
git diff --check: ok
rtk python -m pytest -q: 412 passed
rtk python -m ruff check .: ok
rtk python -m ruff format --check .: ok
```

Focused validation:

```text
rtk python -m pytest tests/test_cli.py -q: 82 passed
```

## Known Limitations

- The new profiles are intentionally conservative first-pass filters, not final production classifiers.
- BOPV already showed generic-profile overmatch: `81 / 489 = 16.56%`.
- BOA still has ingestion-side `DOCS=1-250` cap risk; candidate dry-run should stop if the metadata window contains any date at that cap.
- DOGC still needs separate operational confidence on TLS/connectivity and pagination before broad candidate operations.
- BORM candidate dry-run is meaningful only after a real BORM metadata backfill exists for the target date range.

## BOPV Dry-Run Readiness

BOPV can now be rerun through the real CLI:

```bash
official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOPV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile bopv-ayudas \
  --dry-run \
  --limit 200
```

This should remain dry-run only. Do not create BOPV candidates until the profile dry-run result is reviewed.

# BOPV Candidate Profile Dry-Run - 2026-05-23

## Scope

Reran the BOPV/EHAA candidate dry-run on the VPS through the real `find-source-candidates` CLI after adding:

- `BOPV` source support;
- `bopv-ayudas` profile support.

This was dry-run only.

No candidates were created. No artifacts were downloaded. No downstream writes were performed.

## Deployed Commit

```text
69b39fc
```

## Command

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

## Previous Workaround Result

The prior BOPV read-only workaround used the generic `la-ayuda` profile because the CLI did not yet support `--source BOPV`.

```text
documents_scanned=489
matches_total=117
matches_after_filters=81
match_rate=16.56%
source_candidates unchanged
artifact_download_attempts unchanged
DB valid
```

Conclusion from the workaround:

```text
generic la-ayuda overmatched BOPV metadata
```

## New CLI/Profile Result

Real CLI result with `bopv-ayudas`:

| Metric | Value |
| --- | ---: |
| Documents scanned | 489 |
| Matches total before filters | 177 |
| Matches after filters | 1 |
| Documents matched | 1 |
| Candidates created | 0 |
| Candidates skipped existing | 0 |
| Excluded by section | 0 |
| Excluded by department | 0 |
| Excluded by keyword rules | 176 |
| Sample count | 1 |
| Filtered match rate | 0.20% |

Keyword distribution after filters:

```text
ayudas:1
convocatoria:1
discapacidad:1
empleo:1
```

Section distribution after filters:

```text
OTRAS_DISPOSICIONES:1
```

Department distribution after filters:

```text
LANBIDE-SERVICIO_PUBLICO_VASCO_DE_EMPLEO:1
```

Sample match:

```text
official_identifier=BOPV:BOPV-2026-04-2601788a
matched_keywords=ayudas,convocatoria,empleo,discapacidad
section=OTRAS_DISPOSICIONES
```

## Reduction

Previous filtered result:

```text
81 / 489 = 16.56%
```

New filtered result:

```text
1 / 489 = 0.20%
```

Reduction in filtered matches:

```text
80 fewer matches
98.77% reduction
```

## Noise Observations

The profile is intentionally conservative.

Good:

- It removed the broad BOPV generic-profile overmatch.
- It excluded weak/generic `ayudas`, `subvenciones`, `convocatoria`, `vivienda`, `empleo` and sectoral/procedural patterns unless paired with direct citizen/student/family signals.
- It produced zero candidate writes.

Risk:

- `1 / 489` may be too conservative.
- The remaining match includes `empleo` in a Lanbide department context plus `discapacidad`; it needs human metadata review before any candidate write.
- Some legitimate BOPV aids may be missed until the profile is tuned against real positive/negative samples.

## Safety Checks

Post-run checks:

| Check | Result |
| --- | --- |
| BOPV official_documents | 489 |
| source_candidates | 146 |
| artifact_download_attempts | 482 |
| artifact size | 28,857,411 bytes |
| DB validation | `status=valid`, schema version `8` |
| MCP privacy | no `official`, `mcp`, `python`, `uvicorn` or `fastmcp` listeners |

No writes were observed:

- `source_candidates` unchanged;
- `artifact_download_attempts` unchanged;
- artifact size unchanged.

## Candidate Creation Decision

Do not create BOPV candidates yet.

The new profile reduced overmatch strongly, but the result may now be too narrow. The next step should inspect the one surviving match and a sample of excluded high-signal BOPV rows before any `--write`.

## Recommended Next Task

```text
TASK-AUTO-BOPV-004B - BOPV profile calibration review
```

Scope:

- review the one included match;
- review a small sample of excluded BOPV documents with strong keywords;
- identify false negatives from `bopv-ayudas`;
- adjust profile only if the sample shows legitimate missed citizen/student/family aids;
- rerun dry-run after any refinement;
- still do not create candidates.

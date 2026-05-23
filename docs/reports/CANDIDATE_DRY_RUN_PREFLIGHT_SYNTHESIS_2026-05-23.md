# Candidate Dry-Run Preflight Synthesis - 2026-05-23

## Scope

Integrated the BOPV candidate dry-run report and local candidate dry-run readiness reports for BOA, DOGC and BORM.

Branches merged:

- `agent/boa-004-prep`
- `agent/dogc-004-prep`
- `agent/borm-004-prep`

BOPV report was pushed directly to `main` before this synthesis:

- `docs/reports/BOPV_30_DAY_CANDIDATE_DRY_RUN_2026-05-23.md`

No additional VPS operation was executed by the supervisor.

## BOPV Dry-Run Result

The intended CLI command was attempted on VPS:

```text
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOPV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 200
```

Result:

```text
blocked before scan: argument --source invalid choice: BOPV
```

To preserve the no-write constraint, the agent used an equivalent read-only inspection through the deployed matching functions and a SQLite `mode=ro` connection.

Metrics:

| Metric | Value |
| --- | ---: |
| BOPV documents scanned | 489 |
| Matches before filters | 117 |
| Raw match rate | 23.93% |
| Matches after filters | 81 |
| Filtered match rate | 16.56% |
| Excluded by keyword rules | 36 |
| Candidates created | 0 |
| source_candidates | 146 -> 146 |
| artifact_download_attempts | 482 -> 482 |

Safety:

- DB validation on VPS: valid.
- Artifact size unchanged.
- MCP privacy check: no `official`, `mcp`, `python`, `uvicorn` or `fastmcp` listeners.

Conclusion:

```text
BOPV overmatches with the generic la-ayuda profile.
Do not create BOPV candidates yet.
```

BOPV needs two local changes before any candidate write:

- add `BOPV` to `find-source-candidates --source`;
- add a source-specific `bopv-ayudas` profile and tests.

## BOA Readiness

BOA candidate dry-run is not ready today.

Current blocker:

```text
find-source-candidates --source BOA is not supported
```

Known candidate-stage risks:

- no BOA-specific profile exists;
- generic `la-ayuda` is likely to overmatch awards, appointments, public-entity grants, employment and correction notices;
- BOA ingestion has a known `DOCS=1-250` cap risk and should stop if any date reaches `documents_fetched=250`;
- BOA candidate dry-run is meaningful only after a real BOA metadata window has been ingested and validated.

Next safe BOA task:

```text
add BOA source support to find-source-candidates, add focused tests, and prepare a BOA-specific profile
```

## DOGC Readiness

DOGC candidate dry-run is not ready today.

Current blockers:

- `find-source-candidates --source DOGC` is not supported;
- no `dogc-ayudas` profile exists;
- no validated DOGC 30-day VPS metadata window exists.

Additional risks:

- prior local live probe hit TLS handshake failure before HTTP status;
- DOGC date search currently uses `page=1` and `numResultsByPage=100` without pagination;
- Catalan metadata requires DOGC-specific keyword and exclusion rules;
- live date/search/document identifier stability still needs VPS confirmation.

Sequencing:

```text
DOGC should run after BOA and BORM for candidate dry-run preparation.
```

## BORM Readiness

BORM candidate dry-run is not ready today.

Current blocker:

```text
find-source-candidates --source BORM is not supported
```

Known risks:

- no `borm-ayudas` profile exists;
- generic subsidy keywords may overmatch administrative announcements;
- candidate dry-run is only meaningful after a real BORM metadata backfill exists for the target range;
- BORM current-year XML strategy is acceptable for a current 30-day window, but not broad historical/cross-year usage without archived annual resources.

Relative readiness:

```text
BORM is the safest next metadata backfill candidate among BOA, DOGC and BORM.
BORM is not yet safe as the next candidate dry-run target until CLI source support and profile tests exist.
```

## Recommended Next Single Operation

Do not create candidates yet.

Recommended next task:

```text
TASK-CANDIDATE-SOURCES-001 - Add candidate dry-run source support and source profiles for BOPV/BOA/BORM/DOGC
```

Recommended scope:

- add `BOPV`, `BOA`, `BORM`, and `DOGC` to `find-source-candidates --source`;
- add focused CLI tests proving each source is accepted;
- add or scaffold source-specific profiles:
  - `bopv-ayudas`
  - `boa-ayudas`
  - `borm-ayudas`
  - `dogc-ayudas`
- test that `--dry-run` creates zero `source_candidates`;
- keep write mode gated behind explicit `--write`;
- do not run VPS candidate creation;
- do not download artifacts;
- do not write downstream.

Recommended operational sequencing after that local task:

1. Repeat BOPV dry-run through the real CLI using `bopv-ayudas`.
2. If BOPV match rate is reasonable, prepare a limited BOPV candidate batch proposal.
3. If expanding metadata before candidates, run BORM 30-day metadata backfill as the next serial VPS operation.
4. Defer DOGC operational dry-runs until TLS/pagination concerns are resolved.

## Branch Cleanup

Safe to delete after this synthesis is pushed:

- `agent/boa-004-prep`
- `agent/dogc-004-prep`
- `agent/borm-004-prep`

The BOPV-004 report was already pushed to `main`; no BOPV-004 branch cleanup is required from this supervisor pass.

## Guardrails

- No candidate writes until source-specific dry-runs show acceptable noise.
- No `--write` unless explicitly authorized.
- No artifact downloads during candidate dry-runs.
- No downstream writes during source candidate measurement.
- VPS operations remain serial.

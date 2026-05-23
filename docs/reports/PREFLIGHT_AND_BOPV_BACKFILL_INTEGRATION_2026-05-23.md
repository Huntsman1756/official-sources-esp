# Preflight and BOPV Backfill Integration - 2026-05-23

## Scope

Integrated the BOPV operational report plus BOA, DOGC and BORM local preflight reports.

Branches reviewed and merged:

- `agent/boa-003-prep`
- `agent/dogc-003-prep`
- `agent/borm-003-prep`
- `agent/bopv-003-backfill`

No additional VPS ingestion was executed by the supervisor.

## Merge Result

Merge order:

1. `agent/boa-003-prep`
2. `agent/dogc-003-prep`
3. `agent/borm-003-prep`
4. `agent/bopv-003-backfill`

Conflicts:

- none

All four branches were report-only:

- `docs/reports/BOA_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/DOGC_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/BORM_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/BOPV_30_DAY_METADATA_BACKFILL_2026-05-23.md`

## Validation

Supervisor validation after merge:

```text
git diff --check: ok
rtk python -m pytest -q: 411 passed
rtk python -m ruff check .: ok
rtk python -m ruff format --check .: ok
```

## BOPV Backfill Result

Operational source:

```text
BOPV/EHAA
```

Deployed commit:

```text
c10ff19
```

Range:

```text
2026-04-21 -> 2026-05-20
```

Result:

| Metric | Value |
| --- | ---: |
| Dates processed | 30 |
| Success | 20 |
| No publication | 10 |
| Failed | 0 |
| Documents fetched | 489 |
| Documents new | 489 |
| Documents updated | 0 |
| BOPV official_documents | 0 -> 489 |
| BOPV ingestion_runs | 0 -> 30 |
| source_candidates | 146 -> 146 |
| artifact_download_attempts | 482 -> 482 |

DB validation:

```text
before: status=valid, schema version 8
after: status=valid, schema version 8
```

Backups:

- pre-run: `/opt/official-sources/data/backups/official_sources_before_bopv_30d_backfill_20260523_202155.sqlite`
- post-run: `/opt/official-sources/data/backups/official_sources_after_bopv_30d_backfill_20260523_202357.sqlite`

MCP privacy:

```text
no official/mcp/python/uvicorn/fastmcp listeners returned by the privacy check
```

Conclusion:

```text
BOPV is ready for a candidate dry-run, but not for candidate writes yet.
```

## BOA Preflight Result

Local smoke:

| Date | Status | Documents |
| --- | --- | ---: |
| 2026-01-28 | success | 54 |
| 2026-01-25 | no_publication | 0 |

Local DB validation:

```text
status=valid
```

Safety result:

- `source_candidates=0`
- `artifact_download_attempts=0`
- only metadata/raw API response records in temp DB

Main risk:

```text
BOA currently requests DOCS=1-250 and has no implemented pagination guard.
```

Stop condition for future VPS run:

```text
stop if any date returns documents_fetched=250
```

Readiness:

```text
Ready for a controlled metadata-only VPS backfill after explicit approval.
```

## DOGC Preflight Result

Local smoke:

| Date | Status | Documents |
| --- | --- | ---: |
| 2026-05-22 | success | 2 |
| 2026-05-23 | no_publication | 0 |

Local DB validation:

```text
status=valid
```

Safety result:

- `source_candidates=0`
- `artifact_download_attempts=0`
- only metadata/raw API response records in temp DB

Main risks:

- `searchDOGC` currently uses `page=1` and `numResultsByPage=100`, without pagination.
- Local live probe hit an SSL/TLS handshake failure before HTTP status.

Readiness:

```text
Conditionally ready only after a single-date VPS live smoke succeeds.
```

DOGC should not be the next broad unattended backfill until pagination/connectivity behavior is verified on VPS.

## BORM Preflight Result

Local smoke:

| Date | Status | Documents |
| --- | --- | ---: |
| 2026-05-20 | success | 41 |
| 2026-05-17 | no_publication | 0 |

Local DB validation:

```text
valid=True
```

Safety result:

- `source_candidates=0`
- `artifact_download_attempts=0`
- `pdf_files=0`
- `raw_snapshots=41`

Main risks:

- BORM uses a current-year XML index.
- The strategy is acceptable for a May 2026 30-day window, but not for broad historical or cross-year backfills without annual archived resources.
- There is no official pagination/total reconciliation signal.

Readiness:

```text
Ready for a supervised 30-day metadata-only VPS backfill after explicit approval.
```

## Recommended Next Single VPS Operation

Do not run another VPS operation automatically from this integration pass.

Recommended next task:

```text
TASK-AUTO-BOPV-004 - BOPV candidate dry-run
```

Reason:

- BOPV already has real VPS metadata for the target 30-day range.
- Backfill was clean: 30 dates, 0 failures, DB valid, no candidates/artifacts changed.
- The next step should be read-only candidate quality measurement before any candidate creation.

Suggested command class:

```text
official-sources find-source-candidates --source BOPV --date-from 2026-04-21 --date-to 2026-05-20 --profile la-ayuda --dry-run
```

The profile may overmatch and should be treated as measurement only.

Alternative next backfill if the decision is to expand metadata coverage before BOPV candidates:

```text
TASK-AUTO-BORM-003 - Controlled BORM 30-day metadata backfill
```

BORM is currently the cleanest next metadata backfill candidate among BOA, DOGC and BORM. BOA is also viable but needs the `documents_fetched=250` stop condition. DOGC should wait for a VPS single-date live smoke because of the TLS and pagination risks.

## Branch Cleanup

Safe to delete after this synthesis is pushed:

- `agent/bopv-003-backfill`
- `agent/boa-003-prep`
- `agent/dogc-003-prep`
- `agent/borm-003-prep`

## Guardrails For Next Phase

- VPS operations stay serial.
- Candidate dry-runs can be read-only.
- Candidate writes require a fresh backup and explicit approval.
- Artifact downloads remain separate from candidate dry-runs.
- Downstream writes remain separate from official-source operations.

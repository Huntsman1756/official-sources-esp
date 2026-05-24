# Next Operations Synthesis

Date: 2026-05-24

Scope: integrate the BORM candidate batch result and the parallel preparation reports for BOA, DOGC, and BOPV.

No additional VPS operation was executed during this synthesis. No candidates were created beyond `TASK-AUTO-BORM-006`. No artifacts were downloaded. No downstream project was touched.

## Inputs

Operational result:

```text
docs/reports/BORM_30_DAY_CANDIDATE_BATCH_2026-05-23.md
```

Parallel preparation reports:

```text
docs/reports/BOA_NEXT_OPERATION_PREP_2026-05-24.md
docs/reports/DOGC_SMOKE_PREP_2026-05-24.md
docs/reports/BOPV_EVIDENCE_DOWNLOAD_PREFLIGHT_2026-05-24.md
```

## BORM Result

`TASK-AUTO-BORM-006` completed successfully as the only VPS/DB operation in this pass.

```text
source=BORM
profile=borm-ayudas
range=2026-04-21 -> 2026-05-20
limit=13
deployed_commit=5d76754
source_candidates_total=150 -> 163
BORM source_candidates=0 -> 13
BORM review_status_distribution=human_review_required:13
artifact_download_attempts=482 -> 482
artifact_size=30M -> 30M
DB validation=valid
MCP privacy=no matching listeners
```

Created BORM candidate IDs:

```text
151,152,153,154,155,156,157,158,159,160,161,162,163
```

Recommended next BORM task:

```text
TASK-AUTO-BORM-007 — BORM candidate triage
```

Scope should remain metadata-only:

```text
no artifact downloads
no review_status changes
no downstream writes
```

## BOA Readiness

The BOA prep report concludes that the next BOA operation should be:

```text
TASK-AUTO-BOA-004 — Controlled BOA 30-day metadata backfill
```

Reason:

```text
BOA adapter and runbook exist, but there is no recorded completed BOA 30-day metadata window in VPS.
BOA candidate dry-run should wait until the metadata backfill exists and is validated.
```

Important BOA stop condition:

```text
stop if any date reaches documents_fetched=250 or shows API limit/pagination risk
```

BOA is ready for a single supervised VPS metadata-only backfill, but it should not run in parallel with BORM triage or any other VPS/DB operation.

## DOGC Readiness

DOGC should not go directly to a 30-day backfill.

Recommended next DOGC operation:

```text
TASK-AUTO-DOGC-004 — DOGC VPS smoke
```

Prepared dates:

```text
published_date=2026-05-22
no_publication_date=2026-05-23
```

DOGC 30-day backfill should be allowed only after the smoke verifies:

```text
DB validation before/after
no TLS/connectivity issues
no pagination/page-size risk
stable DOGC:<CVE> identifiers
no candidates
no artifact_download_attempts
no downstream writes
```

## BOPV Evidence Readiness

BOPV has selected candidates for future evidence:

```text
candidate_ids=147,149,150
```

Recommended evidence type:

```text
xml,html
```

PDF should remain deferred.

Current blocker:

```text
BOPV artifact downloader support is not implemented.
```

The preflight found that `download-source-artifacts --source` currently accepts BOE, BOJA, DOGV, and BOCYL, but not BOPV. Before any BOPV evidence download, implement scoped BOPV downloader support with explicit `--candidate-ids`, source validation, and XML/HTML-first behavior.

Recommended BOPV task:

```text
TASK-AUTO-BOPV-007-PREP — Add scoped BOPV XML/HTML artifact downloader support
```

Do not run BOPV evidence download until that support exists and passes tests.

## Recommended Next Single VPS Operation

Recommended immediate next operation:

```text
TASK-AUTO-BORM-007 — BORM candidate triage
```

Reason:

```text
BORM candidates now exist and should be classified before evidence or downstream planning.
It is metadata-only, reads the real DB, and should be done by one agent.
```

Second-best next VPS operation if prioritizing source coverage instead of BORM triage:

```text
TASK-AUTO-BOA-004 — Controlled BOA 30-day metadata backfill
```

DOGC should wait for smoke. BOPV evidence should wait for downloader implementation.

## Prepared But Not Executed

```text
BOA 30-day metadata backfill runbook: ready
DOGC VPS smoke plan: ready
BOPV selected evidence download: blocked on downloader support
```

## Branches Integrated

Reports integrated from:

```text
origin/codex/boa-next-operation-prep
origin/codex/dogc-smoke-prep
origin/codex/bopv-evidence-preflight
```

Integration method:

```text
new report files were taken from the branches
older branch snapshots were not allowed to overwrite the newer BORM-006 main docs
```

## Branches Safe To Delete

After confirming `main` contains the reports:

```text
codex/boa-next-operation-prep
codex/dogc-smoke-prep
codex/bopv-evidence-preflight
```

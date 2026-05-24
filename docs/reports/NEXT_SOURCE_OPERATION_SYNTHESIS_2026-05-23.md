# Next Source Operation Synthesis

Date: 2026-05-24

Scope: integrate the BOPV metadata-only candidate triage and the BOA, BORM, and DOGC runbooks prepared in parallel.

No VPS ingestion was run by this synthesis. No candidates were created. No artifacts were downloaded. No downstream project was touched.

## Branches Integrated

```text
codex/boa-backfill-runbook
codex/borm-backfill-runbook
codex/dogc-vps-smoke-runbook
codex/bopv-candidate-triage
```

Merge conflicts:

```text
none
```

## BOPV Triage Result

Input candidates:

```text
147,148,149,150
```

Distribution:

```text
reviewed=4
likely_relevant=1
unclear=2
out_of_scope=1
false_positive=0
```

Selected for future scoped evidence download:

```text
147,149,150
```

Candidate `148` should not be included in the next evidence batch unless institutional research grants are explicitly in scope.

Safety checks from the BOPV triage:

```text
source_candidates_total=150
BOPV source_candidates=4
BOPV review_status_distribution=human_review_required:4
artifact_download_attempts=482
artifact_bytes=28857411
DB validation=status=valid schema_version=8
MCP privacy=no matching official/mcp/python/uvicorn/fastmcp listeners
```

## BOA Readiness

BOA has a complete 30-day metadata-only VPS runbook:

```text
docs/reports/BOA_BACKFILL_RUNBOOK_2026-05-23.md
```

Readiness:

```text
ready for separately approved VPS execution
```

Main risk:

```text
BOA JSON endpoint uses DOCS=1-250; stop if documents_fetched reaches 250 or API limit risk appears.
```

Operational posture:

```text
metadata-only
serial per-date loop
pre/post backup
DB validation
no candidates
no artifacts beyond expected raw API response rows
no downstream
```

## BORM Readiness

BORM has a complete 30-day metadata-only VPS runbook:

```text
docs/reports/BORM_BACKFILL_RUNBOOK_2026-05-23.md
```

Readiness:

```text
ready for separately approved VPS execution
```

Main risk:

```text
current-year XML index strategy; safe for the recent target window, not for older historical windows or year-boundary backfills without archive review.
```

Operational posture:

```text
metadata-only
serial per-date loop
pre/post backup
DB validation
no candidates
no PDF/XML/HTML artifact downloads
no downstream
```

## DOGC Risk Status

DOGC has a cautious VPS smoke runbook:

```text
docs/reports/DOGC_VPS_SMOKE_RUNBOOK_2026-05-23.md
```

Readiness:

```text
not ready for unattended 30-day backfill
ready only for a single-date VPS smoke plus one no-publication test
```

Main risks:

```text
TLS/connectivity from VPS
pagination/completeness
calendarDOGC/searchDOGC date agreement
CVE-backed identifier stability
```

DOGC should not be selected for a full backfill until the smoke proves VPS connectivity, date behavior, raw response storage, and CVE-backed identifiers.

## Recommended Next Single VPS Operation

Recommended next operation:

```text
TASK-AUTO-BORM-004 — Controlled BORM 30-day metadata backfill
```

Reasoning:

- BORM is ready for controlled metadata-only execution.
- BORM has no known first-page `250` ceiling like BOA.
- DOGC still needs a VPS smoke before broad execution.
- BOPV should pause until evidence download is explicitly approved for selected candidates.

Fallback if BORM is not approved:

```text
TASK-AUTO-BOA-004 — Controlled BOA 30-day metadata backfill
```

With hard stop:

```text
documents_fetched >= 250
```

Do not run BORM and BOA in the same pass.

## Branch Cleanup

Safe to delete after this synthesis is merged and pushed:

```text
codex/boa-backfill-runbook
codex/borm-backfill-runbook
codex/dogc-vps-smoke-runbook
codex/bopv-candidate-triage
```

Also safe to remove local worktrees after confirming no unpushed changes remain:

```text
G:\_Proyectos\mcpspain\official-sources-bopv-triage
G:\_Proyectos\mcpspain\official-sources-next-source-synthesis
```

## Validation

Required for this docs-only integration:

```text
rtk git diff --check
```

No pytest or ruff run is required because this synthesis contains documentation only.

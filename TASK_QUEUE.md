# Task Queue

Last updated: 2026-05-24

This file was absent at the start of `TASK-SOURCE-REGISTRY-001`. It is now the local task queue
for source-platform work in this repository.

## Completed

| Task | Status | Notes |
| --- | --- | --- |
| `TASK-SOURCE-PLATFORM-001` | accepted | Cross-project boundary accepted in `PROJECT_STATE.md` and `docs/CROSS_PROJECT_INTEGRATION_MAP.md`. |
| `TASK-SOURCE-REGISTRY-001` | implemented locally | Canonical executable registry added at `config/sources.yaml`, with validation tests and read-only CLI coverage reporting. |

## Next

| Task | Status | Boundary |
| --- | --- | --- |
| `TASK-SOURCE-RSS-MONITOR-001` | proposed | Separate task only; do not implement RSS/Atom monitoring as part of the source-registry task. Suggested pilots: BOCYL first, BOE as a secondary positive control. |

## Guardrails

- Do not create source candidates by default.
- Do not create evidence-grade records by default.
- Do not download PDFs without explicit scoped artifact commands.
- Do not run broad backfills from registry work.
- Do not write to downstream product repositories.
- Do not run VPS or production DB operations unless a separate task explicitly authorizes them.

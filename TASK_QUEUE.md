# Task Queue

Last updated: 2026-05-24

This file was absent at the start of `TASK-SOURCE-REGISTRY-001`. It is now the local task queue
for source-platform work in this repository.

## Completed

| Task | Status | Notes |
| --- | --- | --- |
| `TASK-SOURCE-PLATFORM-001` | accepted | Cross-project boundary accepted in `PROJECT_STATE.md` and `docs/CROSS_PROJECT_INTEGRATION_MAP.md`. |
| `TASK-SOURCE-REGISTRY-001` | implemented locally | Canonical executable registry added at `config/sources.yaml`, with validation tests and read-only CLI coverage reporting. |
| `TASK-SOURCE-RSS-MONITOR-001` | implemented locally | Metadata-only RSS/Atom discovery monitor added with BOCYL as pilot. Default mode is preview; JSONL writes require explicit `--write`. |
| `TASK-MCP-SOURCE-COVERAGE-001` | implemented locally | Read-only MCP tools expose registry coverage and existing RSS discovery JSONL without live fetches or writes. |
| `TASK-SOURCE-RSS-MONITOR-002` | implemented locally | BOE RSS and BOJA Atom feeds added as validated metadata-only discovery sources. |
| `TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001` | implemented locally | Canonical Coverage v1 snapshot added from the executable registry and current monitor/MCP capabilities. |

## Next

| Task | Status | Boundary |
| --- | --- | --- |
| `TASK-SOURCE-BOPV-API-001` | proposed | Separate task only; do not implement BOPV REST/API discovery from RSS monitor work. |
| `TASK-SOURCE-RSS-MONITOR-003` | proposed | Only after selecting 2-3 verified official RSS/Atom feeds; keep discovery metadata-only. |
| `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` | proposed | Generate safe sample discovery outputs only if needed; avoid live writes unless explicitly scoped. |

## Guardrails

- Do not create source candidates by default.
- Do not create evidence-grade records by default.
- Do not download PDFs without explicit scoped artifact commands.
- Do not run broad backfills from registry work.
- Do not treat RSS/Atom discovery records as evidence or candidates.
- Do not fetch live feeds through MCP source-coverage tools.
- Do not write to downstream product repositories.
- Do not run VPS or production DB operations unless a separate task explicitly authorizes them.
- Do not expand candidates or evidence-grade workflows without explicit approval.

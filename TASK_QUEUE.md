# Task Queue

Last updated: 2026-05-26

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
| `TASK-SOURCE-BOPV-API-001` | implemented locally | Metadata-only BOPV REST/API discovery adapter added for the official Open Data Euskadi endpoint. |
| `TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001` | implemented locally | Coverage v1.1 snapshot added after BOPV API discovery; MCP API JSONL exposure remains future work. |
| `TASK-MCP-API-DISCOVERY-OUTPUT-001` | implemented locally | Read-only MCP latest discovery reader now supports existing RSS and API monitor JSONL output. |
| `TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001` | implemented locally | Integration check validates registry, RSS monitor, API monitor, and MCP coverage/discovery together. |
| `TASK-MCP-COVERAGE-USAGE-DOCS-001` | implemented locally | Usage guide documents registry CLI, RSS/API discovery previews, MCP coverage tools, and safety boundaries. |
| `TASK-SOURCE-COVERAGE-SCHEDULE-001` | implemented locally | Controlled discovery run plan added; one source at a time, preview by default, explicit write only, report template included. |
| `TASK-SOURCE-RSS-MONITOR-003` | implemented locally | BOIB, BOC_CANTABRIA, and DOE RSS feeds added as validated metadata-only discovery sources; DOGC and BON were checked but not added. |
| `TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001` | implemented locally | Coverage v1.2 snapshot added after RSS-003; current coverage is six RSS/Atom sources, one API discovery source, and no candidate/evidence expansion. |
| `TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001` | implemented locally | Source-tree CLI validation now works through `python -m official_sources.cli`; docs explain stale console script handling and editable reinstall. |
| `TASK-SOURCE-OFFICIAL-DIRECTORY-001` | implemented locally | Reconciled `config/sources.yaml` against BOE/PAG official bulletin directories and added 43 provincial bulletin entries as `inventory_only` only. |
| `TASK-SOURCE-COVERAGE-V1.3-SNAPSHOT-001` | implemented locally | Coverage v1.3 snapshot added after official directory reconciliation; current registry has 65 sources, including 43 provincial inventory-only entries. |
| `TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001` | implemented locally | BOP_A_CORUNA HTML discovery pilot added as metadata-only, one-source monitoring; no candidates/evidence/PDFs/artifacts/downstream writes. |
| `TASK-SOURCE-COVERAGE-V1.4-SNAPSHOT-001` | implemented locally | Coverage v1.4 snapshot added after the BOP_A_CORUNA provincial HTML pilot; current coverage is 6 RSS/Atom, 1 API, and 1 HTML provincial discovery source. |
| `TASK-MCP-HTML-DISCOVERY-OUTPUT-001` | implemented locally | Read-only MCP latest discovery reader now supports existing HTML monitor JSONL output alongside RSS/API output. |
| `TASK-MCP-DISCOVERY-PREVIEW-001` | implemented locally | MCP now exposes controlled one-source metadata-only discovery previews for RSS/API/HTML, with no writes, candidates, evidence-grade records, PDFs/artifacts, backfills, or downstream writes. |
| `TASK-MCP-COVERAGE-RECOMMENDATIONS-001` | implemented locally | MCP now recommends next source work deterministically from registry/cache state, without LLMs, live fetches, previews, writes, candidates, evidence-grade records, or downstream writes. |
| `TASK-SOURCE-PROVINCIAL-DISCOVERY-002` | implemented locally | Evaluated BOP_ALBACETE, BOP_ALICANTE, and BOP_ALMERIA from MCP recommendations; added metadata-only HTML discovery for BOP_ALBACETE and BOP_ALICANTE; left BOP_ALMERIA inventory-only due ZK/JavaScript surface. |

## Next

| Task | Status | Boundary |
| --- | --- | --- |
| `TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-002` | proposed | Choose at most 1-2 additional provincial sources after access-path verification; no bulk provincial monitoring. |
| `TASK-SOURCE-PROVINCIAL-URL-DIFF-AUDIT-001` | proposed | Compare BOE and PAG provincial URLs source by source; documentation-only unless a URL correction is verified. |
| `TASK-SOURCE-RSS-MONITOR-004` | proposed | Only after selecting another 2-3 verified official RSS/Atom feeds; keep discovery metadata-only. |
| `TASK-SOURCE-HTML-MONITOR-PILOT-001` | proposed | Only for sources without RSS/API, after source-specific endpoint/robots/fixture audit. |
| `TASK-SOURCE-COVERAGE-RUN-REPORT-001` | proposed | Only if actual metadata-only JSONL writes are run; document source, date, output path, row count, and guardrails. |
| `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` | proposed | Generate safe sample discovery outputs only if needed; avoid live writes unless explicitly scoped. |
| `TASK-SOURCE-COVERAGE-V1.5-SNAPSHOT-001` | proposed | Snapshot coverage after BOP_ALBACETE and BOP_ALICANTE HTML discovery promotion. |
| `TASK-SOURCE-PROVINCIAL-DISCOVERY-003` | proposed | Only after v1.5 snapshot; evaluate at most 2 more provincial sources, no bulk monitoring. |

## Guardrails

- Do not create source candidates by default.
- Do not create evidence-grade records by default.
- Do not download PDFs without explicit scoped artifact commands.
- Do not run broad backfills from registry work.
- Do not treat RSS/Atom discovery records as evidence or candidates.
- Do not fetch live feeds through MCP source-coverage tools.
- Do not fetch live API data through MCP source-coverage tools.
- Do not write to downstream product repositories.
- Do not run VPS or production DB operations unless a separate task explicitly authorizes them.
- Do not expand candidates or evidence-grade workflows without explicit approval.

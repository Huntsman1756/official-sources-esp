# Task Queue

Last updated: 2026-05-27

This file was absent at the start of `TASK-SOURCE-REGISTRY-001`. It is now the local task queue
for source-platform work in this repository.

## Completed

Status note: older `implemented locally` rows are historical accepted work in this repository.
Rows marked `closed in main` have been explicitly reconciled against current `main`.

| Task | Status | Notes |
| --- | --- | --- |
| `TASK-SOURCE-PLATFORM-001` | accepted | Cross-project boundary accepted in `PROJECT_STATE.md` and `docs/CROSS_PROJECT_INTEGRATION_MAP.md`. |
| `TASK-SOURCE-REGISTRY-001` | implemented locally | Canonical executable registry added at `config/sources.yaml`, with validation tests and read-only CLI coverage reporting. |
| `TASK-SOURCE-RSS-MONITOR-001` | closed in main | Metadata-only RSS/Atom discovery monitor is present in `main` with BOCYL as the original pilot. Default mode is preview; JSONL writes require explicit `--write`. Current `main` also validates BOE RSS through later RSS/coverage work. |
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
| `TASK-SOURCE-COVERAGE-V1.5-SNAPSHOT-001` | implemented locally | Coverage v1.5 snapshot added after BOP_ALBACETE and BOP_ALICANTE HTML discovery promotion; current coverage is 6 RSS/Atom, 1 API, and 3 HTML provincial discovery sources. |
| `TASK-SOURCE-PROVINCIAL-PATTERN-REPORT-001` | implemented locally | Pattern report compares BOP_A_CORUNA, BOP_ALBACETE, and BOP_ALICANTE; decision is source-specific parsers for now with small shared helpers only. |
| `TASK-SOURCE-PROVINCIAL-HTML-HEALTH-001` | implemented locally | Health check validated BOP_A_CORUNA, BOP_ALBACETE, and BOP_ALICANTE previews without writes; all returned `records=1` with `not_candidate`, `not_evidence`, and `unclassified` safety status. |
| `TASK-VPS-INTEGRITY-CHECK-RAW-METADATA-001` | implemented locally | `integrity-check` now reports `local_path=NULL` metadata rows as `non_local_metadata`, while missing stored local artifact paths still fail. |
| `TASK-DOCS-RSS-MONITOR-STATE-RECONCILIATION-001` | merged | Reconciles RSS monitor documentation with current `main`; confirms RSS-001 should not be reopened and points next implementation work to RSS-004. |
| `TASK-SOURCE-RSS-MONITOR-004` | implemented locally | Adds BOC_CANARIAS, DOG, and BOP_LUGO as validated metadata-only RSS discovery sources; no writes, candidates, evidence-grade records, PDFs, downstream, VPS, Hermes, or systemd changes. |
| `TASK-HERMES-AUDITOR-CANONICAL-ROOT-001` | completed | Hermes now audits `/opt/official-sources/app` through explicit `APP_ROOT`/`REPO_ROOT`/`TARGET_REPO` systemd environment; manual run returned `0/SUCCESS`, failed units are `0`, BOE/integrity/Hermes timers remain active, and report `vps-audit-20260527-044105.md` confirms RSS monitor present and RSS-001 completed. Scheduled validation remains pending next timer run. |
| `TASK-MCP-SOURCE-RANKING-CLEANUP-001` | implemented locally | `recommend_next_sources` now excludes documented blocked/deferred provincial sources such as `BOP_ALMERIA` from the normal ranking while keeping them in registry inventory, and prioritizes Barcelona/Malaga then Bizkaia/Valencia/Sevilla/Zaragoza before alphabetical fallback. No monitors, scraping, writes, VPS, Hermes, timers, candidates, evidence, or downstream changes. |
| `TASK-PROVINCIAL-READONLY-BATCH-AUDIT-001` | implemented locally | Read-only batch audit classified the 38 remaining provincial `inventory_only` sources without documented blockers, using one landing-page request per source. Outputs are `docs/reports/provincial-readonly-batch-audit-2026-05-27.md` and `data/provincial_audit/provincial-readonly-batch-audit-2026-05-27.json`; recommended next pilots are Barcelona, Malaga, Bizkaia, Valencia, and Sevilla. No monitors, registry writes, scraping expansion, candidates, evidence, VPS, Hermes, timers, or downstream changes. |
| `TASK-PROVINCIAL-MONITORS-WAVE-001` | implemented locally | Adds metadata-only source-specific HTML discovery monitors for `BOP_BARCELONA` and `BOP_MALAGA`. Live preview validation on 2026-05-27 returned `records=1` for each with `not_candidate`, `not_evidence`, and `unclassified`; parser validation extracted 20 Barcelona and 19 Malaga current-page records. No PDF/artifact downloads, candidates, evidence-grade records, downstream writes, broad scraping/backfill, VPS, Hermes, systemd, or timer changes. |
| `TASK-PROVINCIAL-MONITORS-WAVE-002` | implemented locally | Adds metadata-only source-specific HTML discovery monitors for `BOP_BIZKAIA` and `BOP_VALENCIA`. Live preview validation on 2026-05-27 returned `records=1` for each with `not_candidate`, `not_evidence`, and `unclassified`; parser validation extracted 34 Bizkaia and 25 Valencia current-page records. No PDF/artifact downloads, candidates, evidence-grade records, downstream writes, broad scraping/backfill, VPS, Hermes, systemd, or timer changes. |
| `TASK-PROVINCIAL-MONITORS-HEALTH-001` | implemented locally | Documentation-only combined live preview health check for monitored provincial sources. Seven sources returned `records=1` in preview mode; `BOP_ALICANTE` failed twice with `httpx.ConnectError: [Errno 11002] getaddrinfo failed` for `sede.diputacionalicante.es`. Overall health decision is NO-GO until Alicante endpoint/DNS is reviewed. No writes, candidates, evidence-grade records, PDFs/artifacts, downstream, VPS, Hermes, systemd, or timer changes. |

## Next

| Task | Status | Boundary |
| --- | --- | --- |
| `TASK-HERMES-AUDITOR-SCHEDULED-VALIDATION-001` | proposed | After the next automatic Hermes timer run, confirm the latest report still targets `/opt/official-sources/app`, reports `main`, clean worktree, RSS monitor present, RSS-001 completed/not current work, and no `Reached maximum iterations` truncation that affects the conclusion. No BOE/integrity/RSS logic changes. |
| `TASK-PROVINCIAL-BOP-ALICANTE-ENDPOINT-HEALTH-001` | proposed | Review the validated `BOP_ALICANTE` backing endpoint after the combined health check failed with DNS resolution errors. Keep it source-specific and read-only; do not alter monitor status or replace URLs unless the official endpoint evidence is revalidated. |
| `TASK-PROVINCIAL-MONITORS-WAVE-003` | proposed | Consider at most 1-2 further metadata-only pilots after Wave 002 is reviewed/merged, with `BOP_SEVILLA` as the next prior audit candidate. Keep source-specific parsers, fixtures/fetchers, preview validation, and no publication/candidate/evidence/PDF/downstream writes. |
| `TASK-SOURCE-PROVINCIAL-URL-DIFF-AUDIT-001` | proposed | Compare BOE and PAG provincial URLs source by source; documentation-only unless a URL correction is verified. |
| `TASK-SOURCE-COVERAGE-V1.6-SNAPSHOT-001` | proposed | Optional snapshot after RSS-004 if current coverage counts need a standalone report. |
| `TASK-SOURCE-RSS-MONITOR-005` | proposed | Only after selecting another 2-3 verified official RSS/Atom feeds; keep discovery metadata-only. |
| `TASK-SOURCE-HTML-MONITOR-PILOT-001` | proposed | Only for sources without RSS/API, after source-specific endpoint/robots/fixture audit. |
| `TASK-SOURCE-COVERAGE-RUN-REPORT-001` | proposed | Only if actual metadata-only JSONL writes are run; document source, date, output path, row count, and guardrails. |
| `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` | proposed | Generate safe sample discovery outputs only if needed; avoid live writes unless explicitly scoped. |
| `TASK-SOURCE-PROVINCIAL-DISCOVERY-003` | proposed | Evaluate at most 2 more provincial sources using the pattern report and health-check criteria; no bulk monitoring and no generic framework unless evidence improves. |
| `TASK-SOURCE-HTML-MONITOR-HELPERS-001` | deferred | Only extract additional shared helpers after another source proves repeated duplication; do not create a broad generic provincial framework yet. |

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

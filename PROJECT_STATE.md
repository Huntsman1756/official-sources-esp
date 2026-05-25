# Project State

Last updated: 2026-05-25

## Current Decision

`TASK-MCP-COVERAGE-RECOMMENDATIONS-001` is implemented locally.

The MCP now exposes a deterministic next-source recommendation tool:

```text
recommend_next_sources(limit=5)
```

Current strategy:

```text
provincial_html_discovery_pilot
```

The tool recommends provincial `inventory_only` sources with official landing URLs and no validated
monitor yet. It excludes already monitored sources such as `BOP_A_CORUNA`, reads existing discovery
cache directory state when present, and returns constraints for metadata-only follow-up work.

This is not an LLM tool and it does not execute previews, fetch live sources, write JSONL, create
files, create candidates, create evidence-grade records, download PDFs/artifacts, mutate
`config/sources.yaml`, touch downstream repos, run backfills, run VPS/prod DB operations, or add LLM
classification.

Report:

```text
docs/reports/mcp-coverage-recommendations-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-MCP-DISCOVERY-PREVIEW-001
```

`TASK-MCP-DISCOVERY-PREVIEW-001` is implemented locally.

The MCP now exposes a controlled one-source discovery preview tool:

```text
preview_discovery(source_code, date, limit=1, discovery_type=None)
```

Supported preview families:

```text
rss: validated RSS/Atom discovery sources
api: BOPV API discovery
html: BOP_A_CORUNA HTML discovery
```

The tool runs preview mode only. It refuses broad/all-source requests, unknown sources,
inventory-only sources without implemented validated monitor support, and `limit > 10`.

Preview results are metadata-only:

```text
mode=preview
output_written=false
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

The tool does not write RSS/API/HTML JSONL, create files, create candidates, create evidence-grade
records, download PDFs/artifacts, mutate `config/sources.yaml`, touch downstream repos, run
backfills, run VPS/prod DB operations, or add LLM classification.

Report:

```text
docs/reports/mcp-discovery-preview-tools-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-MCP-HTML-DISCOVERY-OUTPUT-001
```

`TASK-MCP-HTML-DISCOVERY-OUTPUT-001` is implemented locally.

The MCP latest discovery reader now supports existing HTML monitor JSONL output in addition to RSS
and API output:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

Discovery entries are returned in deterministic order when multiple files exist for the same
source/date:

```text
rss -> api -> html
```

The MCP reader remains read-only. It does not fetch live RSS/API/HTML, write JSONL, create
candidates, create evidence-grade records, download PDFs/artifacts, touch downstream repos, run
backfills, run VPS/prod DB operations, or add LLM classification.

Report:

```text
docs/reports/mcp-html-discovery-output-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.4-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.4-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.4 snapshot after the first provincial HTML discovery pilot:

```text
docs/reports/source-coverage-v1-4-snapshot-2026-05-25.md
```

Coverage v1.4 summarizes the executable registry after `BOP_A_CORUNA` was promoted from provincial
inventory to a single-source HTML discovery pilot:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 4
inventory_only: 51
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API/HTML writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes,
backfills, all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001
```

`TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001` is implemented locally.

The first provincial metadata-only discovery pilot uses `BOP_A_CORUNA`:

```text
source: BOP_A_CORUNA
access: date-scoped official HTML summary page
command: official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 1
output path when explicitly written: data/html_monitor/BOP_A_CORUNA/<YYYY-MM-DD>/html_discovery.jsonl
```

The pilot validates that one provincial bulletin can be observed as metadata-only discovery without
creating candidates, evidence-grade records, PDFs, artifacts, backfills, downstream writes, broad
runs, VPS operations, production DB operations, or LLM classification. The other provincial sources
remain inventory-only.

Current executable registry counts after the pilot:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 4
inventory_only: 51
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Report:

```text
docs/reports/provincial-discovery-pilot-bop-a-coruna-2026-05-25.md
```

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.3-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.3-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.3 snapshot after official directory reconciliation:

```text
docs/reports/source-coverage-v1-3-snapshot-2026-05-24.md
```

Coverage v1.3 summarizes the executable registry after provincial inventory expansion:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 52
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-OFFICIAL-DIRECTORY-001
```

`TASK-SOURCE-OFFICIAL-DIRECTORY-001` is implemented locally.

The executable registry has been reconciled against the official BOE/PAG bulletin directory pages.
The task added provincial bulletin entries as inventory/control-plane records only:

```text
docs/reports/official-directory-registry-reconciliation-2026-05-24.md
```

Current executable registry counts:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 52
paused: 1
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Provincial bulletin entries are official directory inventory only. They are not RSS/API monitors,
not candidates, not evidence, and not validated HTML monitors. The task did not create
source_candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
RSS/API writes, broad monitor runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001
```

`TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001` is implemented locally.

The CLI module entrypoint now works for source-tree validation:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOIB
```

This is the recommended validation path when the installed global `official-sources` console script
is stale. To refresh the local console script, run an editable install from the repository root:

```bash
python -m pip install -e ".[dev]"
```

Report:

```text
docs/reports/cli-entrypoint-consistency-2026-05-24.md
```

This task did not change monitor behavior, registry values, sources, candidates, evidence-grade
records, PDFs, artifacts, downstream writes, backfills, RSS/API writes, VPS operations, production
DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.2 snapshot after RSS monitor expansion 003:

```text
docs/reports/source-coverage-v1-2-snapshot-2026-05-24.md
```

Coverage v1.2 summarizes the executable registry and current RSS/API monitor/MCP capabilities:

```text
total sources: 22
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 9
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

Snapshot caveats:

```text
BOC_CANTABRIA is category-scoped, not complete bulletin coverage.
DOE feed is valid, but RSS-003 live preview returned records=0.
DOGC and BON were not added because tested feed candidates returned 404.
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-003
```

`TASK-SOURCE-RSS-MONITOR-003` is implemented locally.

The RSS/Atom discovery monitor now has six validated feed-backed sources:

```text
BOCYL          rss  https://bocyl.jcyl.es/rss.do
BOE            rss  https://www.boe.es/rss/boe.php
BOJA           atom https://www.juntadeandalucia.es/boja/distribucion/boja.xml
BOIB           rss  https://www.caib.es/eboibfront/es/rss
BOC_CANTABRIA  rss  https://www.cantabria.es/o/BOC/feed/6802081
DOE            rss  https://doe.juntaex.es/rss/rss.php?seccion=6
```

BOIB, BOC_CANTABRIA, and DOE were added as metadata-only discovery sources. Live preview smokes
were run one source at a time with `--limit 1` and without `--write`.

Notes:

```text
BOC_CANTABRIA feed is category-scoped, not complete bulletin coverage.
DOGC was not added because tested candidate RSS URLs returned 404.
BON was not added because tested candidate RSS URLs returned 404.
```

Registry coverage after this task:

```text
total sources: 22
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 9
paused: 1
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

This task did not create source candidates, evidence-grade records, PDFs, artifacts, downstream
writes, backfills, broad/all-source runs, RSS writes, VPS operations, production DB operations,
publication, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-SCHEDULE-001
```

`TASK-SOURCE-COVERAGE-SCHEDULE-001` is implemented locally.

The controlled discovery run plan is documented at:

```text
docs/SOURCE_COVERAGE_RUN_PLAN.md
```

Report:

```text
docs/reports/source-coverage-schedule-2026-05-24.md
```

This task defines safe operation for source discovery monitors:

```text
one source per command
preview by default
--write only when explicitly approved
cache-first JSONL output
run report required for non-trivial executions
no all-source runs
```

It is documentation/control-plane only. It did not add scheduler code, cron, systemd, GitHub
Actions, VPS jobs, new sources, monitor behavior changes, candidates, evidence-grade records, PDFs,
artifacts, downstream writes, backfills, production DB operations, publication, or LLM
classification.

Previous completed source-platform task:

```text
TASK-MCP-COVERAGE-USAGE-DOCS-001
```

`TASK-MCP-COVERAGE-USAGE-DOCS-001` is implemented locally.

The coverage platform usage guide is now documented at:

```text
docs/SOURCE_COVERAGE_USAGE.md
```

It documents:

```text
official-sources sources list
official-sources sources status --source BOCYL
official-sources rss monitor --source BOE/BOJA/BOCYL --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
MCP: list_sources, get_source_status, list_monitorable_sources, list_latest_discovery_entries
```

The documentation restates the coverage safety boundary: RSS/API discovery is metadata-only, MCP is
read-only, monitor writes require explicit `--write`, and coverage commands do not create
candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS operations,
production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001
```

`TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001` is implemented locally.

The coverage platform line was validated on the integration branch:

```text
codex/task-source-coverage-integration-check-001
```

Report:

```text
docs/reports/source-coverage-integration-check-2026-05-24.md
```

Validated together:

```text
config/sources.yaml
RSS/Atom discovery: BOE, BOJA, BOCYL
API discovery: BOPV
MCP read-only coverage/discovery tools
```

Validation results:

```text
sources.yaml total sources: 22
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
RSS previews: BOE, BOJA, BOCYL ok with --limit 1 and no --write
API preview: BOPV ok with --limit 1 and no --write
MCP fixture reads: empty, RSS JSONL, API JSONL, unknown source all ok
python -m pytest -q: 488 passed, 1 warning
```

This task is reporting/control-plane only. It did not create sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-MCP-API-DISCOVERY-OUTPUT-001
```

`TASK-MCP-API-DISCOVERY-OUTPUT-001` is implemented locally.

The MCP/read-only discovery reader now reads existing metadata-only RSS and API discovery JSONL:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
```

The existing MCP tool remains:

```text
list_latest_discovery_entries
```

It now returns `resource_type=discovery_entries`, a `discovery_types` list, `output_paths`, and a
per-entry `discovery_type` marker such as `rss` or `api`.

This task is read-only. It did not add live RSS/API fetching through MCP, JSONL writes, source
candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS operations,
production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.1 snapshot after the BOPV API discovery adapter:

```text
docs/reports/source-coverage-v1-1-snapshot-2026-05-24.md
```

Coverage v1.1 summarizes the executable registry and current RSS/API monitor/MCP capabilities:

```text
total sources: 22
metadata_adapter_validated: 9
inventory_only: 12
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL
API discovery sources: BOPV
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

It also recorded that MCP source coverage still read latest discovery entries from RSS JSONL only;
that gap is now closed by `TASK-MCP-API-DISCOVERY-OUTPUT-001`.

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-BOPV-API-001
```

`TASK-SOURCE-BOPV-API-001` is implemented locally.

BOPV now has a metadata-only REST/API discovery adapter:

```text
src/official_sources/api_monitor.py
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit N
```

The registry declares the official Open Data Euskadi BOPV administrative acts endpoint:

```text
https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}
```

Default behavior is preview-only. JSONL output is written only with explicit `--write`:

```text
data/api_monitor/BOPV/<YYYY-MM-DD>/api_discovery.jsonl
```

A live bounded preview was run one source at a time with `--limit 1` and without `--write`; it
returned `records=1`, `candidate_status=not_candidate`, and `evidence_status=not_evidence`.

This task did not create source candidates, evidence-grade records, PDFs, artifacts, downstream
writes, backfills, broad historical imports, VPS operations, production DB operations, publication,
or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001
```

The project now has a canonical Coverage v1 snapshot:

```text
docs/reports/source-coverage-v1-snapshot-2026-05-24.md
```

Coverage v1 summarizes the executable registry and current monitor/MCP capabilities:

```text
total sources: 22
metadata_adapter_validated: 9
inventory_only: 12
paused: 1
validated RSS/Atom discovery sources: BOCYL, BOE, BOJA
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior, RSS
writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS
operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-002
```

The RSS/Atom discovery monitor now has three validated feed-backed sources:

```text
BOCYL rss  https://bocyl.jcyl.es/rss.do
BOE   rss  https://www.boe.es/rss/boe.php
BOJA  atom https://www.juntadeandalucia.es/boja/distribucion/boja.xml
```

BOE and BOJA were added as metadata-only discovery sources. Live preview smokes were run one source
at a time with `--limit 1` and without `--write`.

No source candidates, evidence-grade records, PDFs, artifacts, downstream writes, VPS operations,
production DB operations, backfills, publication, or LLM classification were added by this task.

DOGC was not added because no stable official RSS/Atom feed was verified for this task. BOPV remains
out of RSS expansion and should stay a separate REST/API task.

Earlier completed source-platform task:

```text
TASK-MCP-SOURCE-COVERAGE-001
```

The MCP/read-only interface now exposes source coverage from the executable registry and
metadata-only RSS discovery output:

```text
list_sources
get_source_status
list_monitorable_sources
list_latest_discovery_entries
```

These MCP tools read:

```text
config/sources.yaml
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

They do not fetch live feeds, create files, create source candidates, create evidence-grade records,
download PDFs, write artifacts, write downstream repos, run VPS operations, run production DB
operations, run backfills, publish data, or add LLM classification.

Earlier completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-001
```

The project now has a metadata-only RSS/Atom discovery monitor:

```text
src/official_sources/rss_monitor.py
official-sources rss monitor --source BOCYL --date YYYY-MM-DD
```

The pilot source is BOCYL through its validated RSS feed:

```text
https://bocyl.jcyl.es/rss.do
```

Default behavior is preview-only. JSONL output is written only with explicit `--write`:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

No source candidates, evidence-grade records, PDFs, artifacts, downstream writes, VPS operations,
production DB operations, backfills, publication, or LLM classification were added by this task.

Earlier completed source-platform task:

```text
TASK-SOURCE-REGISTRY-001
```

The executable canonical source registry remains:


```text
config/sources.yaml
```

The registry is validated by:

```text
tests/test_source_registry.py
```

It is exposed read-only through:

```text
official-sources sources list
official-sources sources status --source BOCYL
```

Previous accepted decision:

```text
TASK-SOURCE-PLATFORM-001
```

Accepted boundary:

```text
official-sources = upstream official-source ingestion and evidence platform
downstream projects = staging + review + product decisions
```

The operative map is:

```text
docs/CROSS_PROJECT_INTEGRATION_MAP.md
```

The supporting report is:

```text
docs/reports/CROSS_PROJECT_INTEGRATION_MAP_2026-05-24.md
```

## Active Boundary

`official-sources` remains the common upstream platform for official source ingestion, evidence,
citations, integrity metadata, scoped artifact availability, candidate/evidence review records,
downstream-ready evidence exports, and alert-grade dry-run/export feeds.

It must not become a downstream product backend.

Hard guardrails:

- No new `oposiciones2.0` write actions from `official-sources`.
- No alert-grade to `source_candidates` conversion.
- No product records created by `official-sources`.
- No notifications, subscriptions, ranking, publication, or product workflow ownership in
  `official-sources`.
- Next allowed platform work must be one source operation at a time.
- Product-local design or preview work must happen inside the downstream repo, not in
  `official-sources`.

## Accepted Task Log

| Task | Status | Decision artifact | Notes |
| --- | --- | --- | --- |
| `TASK-SOURCE-PLATFORM-001` | Accepted | `docs/CROSS_PROJECT_INTEGRATION_MAP.md` | Locks `official-sources` as an upstream official-source ingestion/evidence platform and keeps downstream product decisions out of the platform. |
| `TASK-SOURCE-REGISTRY-001` | Implemented locally | `config/sources.yaml`, `docs/reports/source-registry-2026-05-24.md` | Adds the canonical executable registry for source coverage and status reporting. |
| `TASK-SOURCE-RSS-MONITOR-001` | Implemented locally | `src/official_sources/rss_monitor.py`, `docs/reports/rss-monitor-pilot-2026-05-24.md` | Adds metadata-only RSS/Atom discovery with BOCYL as the pilot source. |
| `TASK-MCP-SOURCE-COVERAGE-001` | Implemented locally | `src/official_sources/source_coverage.py`, `docs/reports/mcp-source-coverage-2026-05-24.md` | Exposes source coverage and existing RSS discovery output through read-only MCP tools. |
| `TASK-SOURCE-RSS-MONITOR-002` | Implemented locally | `config/sources.yaml`, `docs/reports/rss-monitor-expansion-2026-05-24.md` | Adds BOE and BOJA as validated metadata-only RSS/Atom discovery sources. |
| `TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001` | Implemented locally | `docs/reports/source-coverage-v1-snapshot-2026-05-24.md` | Captures the v1 source coverage baseline from the executable registry and read-only MCP/monitor capabilities. |
| `TASK-SOURCE-BOPV-API-001` | Implemented locally | `src/official_sources/api_monitor.py`, `docs/reports/bopv-api-discovery-adapter-2026-05-24.md` | Adds metadata-only BOPV REST/API discovery from the official Open Data Euskadi endpoint. |
| `TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001` | Implemented locally | `docs/reports/source-coverage-v1-1-snapshot-2026-05-24.md` | Captures the v1.1 coverage baseline after adding BOPV API discovery. |
| `TASK-MCP-API-DISCOVERY-OUTPUT-001` | Implemented locally | `src/official_sources/source_coverage.py`, `docs/reports/mcp-api-discovery-output-2026-05-24.md` | Extends the read-only MCP discovery reader to existing RSS and API discovery JSONL. |
| `TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001` | Implemented locally | `docs/reports/source-coverage-integration-check-2026-05-24.md` | Validates the integrated registry, RSS monitor, API monitor, and MCP coverage/discovery line. |
| `TASK-MCP-COVERAGE-USAGE-DOCS-001` | Implemented locally | `docs/SOURCE_COVERAGE_USAGE.md`, `docs/MCP_TOOLS.md`, `README.md` | Documents CLI and MCP source coverage usage with safety boundaries. |
| `TASK-SOURCE-COVERAGE-SCHEDULE-001` | Implemented locally | `docs/SOURCE_COVERAGE_RUN_PLAN.md`, `docs/reports/source-coverage-schedule-2026-05-24.md` | Defines controlled one-source-at-a-time discovery run plan and report template. |
| `TASK-SOURCE-RSS-MONITOR-003` | Implemented locally | `config/sources.yaml`, `docs/reports/rss-monitor-003-verified-feeds-2026-05-24.md` | Adds BOIB, BOC_CANTABRIA, and DOE as validated metadata-only RSS discovery sources; DOGC and BON were not added. |
| `TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001` | Implemented locally | `docs/reports/source-coverage-v1-2-snapshot-2026-05-24.md` | Captures the v1.2 coverage baseline after RSS-003, including six RSS/Atom sources and one API discovery source. |
| `TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001` | Implemented locally | `src/official_sources/cli.py`, `docs/reports/cli-entrypoint-consistency-2026-05-24.md` | Makes `python -m official_sources.cli` usable for source-tree validation and documents stale console script handling. |

## Next Allowed Work

Allowed next work:

1. `TASK-SOURCE-RSS-MONITOR-004` only after selecting another 2-3 verified official RSS/Atom feeds.
2. `TASK-SOURCE-HTML-MONITOR-PILOT-001` only for sources without RSS/API after source-specific audit.
3. `TASK-SOURCE-COVERAGE-RUN-REPORT-001` if actual metadata-only JSONL writes are run.
4. `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` if sample discovery outputs are needed.
5. Product-local design/preview for draft process creation in `oposiciones2.0`.
6. Evidence-grade staging work in `EduAyudas` or `la-ayuda` only after their local states are clean.
7. A source-needs audit for `renta-verificable` before any integration.

Not allowed from this repo:

- downstream writes;
- DB/VPS operations without a separate source-specific task;
- broad imports or backfills;
- alert storage implementation before product storage is approved;
- `oposiciones2.0` product record creation.

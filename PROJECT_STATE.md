# Project State

Last updated: 2026-05-24

## Current Decision

`TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001` is implemented locally.

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

## Next Allowed Work

Allowed next work:

1. `TASK-SOURCE-BOPV-API-001` as a separate BOPV REST/API discovery adapter task if BOPV source expansion is needed.
2. `TASK-SOURCE-RSS-MONITOR-003` only after selecting 2-3 verified official RSS/Atom feeds.
3. `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` if sample discovery outputs are needed.
4. Product-local design/preview for draft process creation in `oposiciones2.0`.
5. Evidence-grade staging work in `EduAyudas` or `la-ayuda` only after their local states are clean.
6. A source-needs audit for `renta-verificable` before any integration.

Not allowed from this repo:

- downstream writes;
- DB/VPS operations without a separate source-specific task;
- broad imports or backfills;
- alert storage implementation before product storage is approved;
- `oposiciones2.0` product record creation.

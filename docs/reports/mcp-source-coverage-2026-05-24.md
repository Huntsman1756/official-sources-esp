# MCP source coverage - 2026-05-24

Task: `TASK-MCP-SOURCE-COVERAGE-001`

## What Was Added

The MCP/read-only interface now exposes the executable source registry and existing
metadata-only RSS discovery output.

Added MCP tools:

- `list_sources`
- `get_source_status`
- `list_monitorable_sources`
- `list_latest_discovery_entries`

These tools are implemented in:

```text
src/official_sources/source_coverage.py
src/official_sources/mcp/tools.py
src/official_sources/mcp/server.py
```

## Data Exposed

`list_sources` returns source coverage summary fields:

- `source_code`
- `name`
- `jurisdiction_level`
- `operational_status`
- `monitor_support`
- `evidence_adapter`

`get_source_status` returns the full registry entry for one `source_code`, including:

- `candidate_creation_allowed`
- `evidence_grade_allowed`
- access methods
- operational status
- support flags
- limitations and notes

It also returns explicit safety metadata:

```text
rss_discovery_is_evidence=false
rss_discovery_is_candidate=false
```

`list_monitorable_sources` returns sources with registry-declared monitor-capable access methods:

```text
rss
atom
api
xml
html
```

Inventory-only sources are not exposed as monitored.

## RSS Discovery Reads

`list_latest_discovery_entries` reads existing JSONL only:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

If `date` is omitted, it selects the latest dated directory that already contains
`rss_discovery.jsonl`.

The tool does not fetch live feeds, run the RSS monitor, or create files. Missing output returns an
empty structured result with:

```text
status=empty
entries=[]
```

Unknown sources return:

```text
status=unknown_source
```

## What Remains Blocked

- Broad/all-source RSS monitoring through MCP remains blocked.
- Live feed fetching through MCP remains blocked.
- RSS discovery records remain metadata-only and not evidence.
- BOPV REST/API discovery remains a separate future task.
- Additional RSS/Atom monitored sources remain a separate task.

## Guardrail Confirmation

This task did not create:

- `source_candidates`
- evidence-grade records
- PDFs
- downloaded source files
- artifact outputs
- backfills
- downstream product writes
- VPS operations
- production DB operations
- live RSS monitor runs
- LLM classification

## Future Tasks

Recommended next task:

```text
TASK-SOURCE-RSS-MONITOR-002 - Add 2-3 more RSS/Atom monitored sources
```

Keep BOPV separate:

```text
TASK-SOURCE-BOPV-API-001 - BOPV REST/API discovery adapter
```

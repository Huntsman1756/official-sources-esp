# MCP API discovery output - 2026-05-24

Task: `TASK-MCP-API-DISCOVERY-OUTPUT-001`

## Scope

This task extends the read-only MCP source coverage discovery reader so it can expose existing API
discovery JSONL output as well as existing RSS discovery JSONL output.

It does not fetch live RSS/API data, create files, create candidates, create evidence-grade
records, download PDFs or artifacts, run backfills, write downstream repositories, run VPS
operations, run production DB operations, or add LLM classification.

## Reader Extended

The existing MCP tool remains:

```text
list_latest_discovery_entries
```

Implementation:

```text
src/official_sources/source_coverage.py
src/official_sources/mcp/tools.py
src/official_sources/mcp/server.py
```

The MCP server tool signature did not gain live-fetch or write parameters.

## Supported Output Paths

The reader now checks existing files in:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
```

If a date is omitted, it resolves the latest existing dated RSS/API output directory for that
source. If no output exists, it returns an empty structured result.

## RSS vs API Identification

The result now returns:

```text
resource_type=discovery_entries
discovery_types=[rss, api]
output_paths={...}
```

Each entry also receives:

```text
discovery_type=rss
```

or:

```text
discovery_type=api
```

If both RSS and API files exist for the same source/date, both are returned. RSS entries are read
first, then API entries, and the global `limit` is applied across the combined result.

## Read-Only Boundary

The MCP reader reads existing JSONL only.

It does not:

- call RSS feed fetchers;
- call API fetchers;
- run monitor commands;
- create or update JSONL output;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- run backfills;
- write downstream repositories.

Safety fields remain metadata-only:

```text
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

The source safety envelope also marks both RSS and API discovery as not evidence and not
candidates.

## Guardrail Confirmation

This task did not create:

- `source_candidates`
- evidence-grade records
- PDFs
- artifact files
- downstream product writes
- backfills
- RSS JSONL writes
- API JSONL writes
- live RSS/API fetches through MCP
- VPS operations
- production DB operations
- LLM classification

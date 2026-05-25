# MCP HTML discovery output - 2026-05-24

Task: `TASK-MCP-HTML-DISCOVERY-OUTPUT-001`

Run date: 2026-05-25

## Scope

This task extended the read-only MCP/source coverage discovery reader so it can expose existing
HTML monitor JSONL output alongside RSS and API output.

It did not add sources, ingestion behavior, monitors, candidates, evidence, artifacts, backfills,
RSS/API/HTML writes, downstream writes, VPS operations, production DB operations, or LLM
classification.

## Reader Extended

The existing MCP tool remains:

```text
list_latest_discovery_entries
```

It now reads existing files from:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

## Discovery Type Assignment

Entries are marked by source file type:

```text
rss_discovery.jsonl  -> discovery_type=rss
api_discovery.jsonl  -> discovery_type=api
html_discovery.jsonl -> discovery_type=html
```

If more than one discovery output exists for the same source/date, entries are returned in
deterministic order:

```text
rss -> api -> html
```

## Read-Only Behavior

The MCP reader reads existing JSONL only.

It does not:

- fetch live RSS feeds;
- fetch live APIs;
- fetch live HTML pages;
- write RSS/API/HTML JSONL;
- run monitors;
- open ingestion repositories;
- create candidates;
- create evidence-grade records;
- download PDFs or artifacts;
- write downstream repositories.

If no discovery output exists, the tool returns an empty structured result with the expected RSS,
API, and HTML output paths.

## Safety Fields

The reader preserves discovery metadata safety fields from the JSONL records:

```text
classification_status=unclassified
candidate_status=not_candidate
evidence_status=not_evidence
```

The source safety envelope also exposes:

```text
rss_discovery_is_candidate=false
rss_discovery_is_evidence=false
api_discovery_is_candidate=false
api_discovery_is_evidence=false
html_discovery_is_candidate=false
html_discovery_is_evidence=false
```

## Tests Added Or Updated

Coverage includes:

- RSS JSONL read still works;
- API JSONL read still works;
- HTML JSONL read works for `BOP_A_CORUNA`;
- missing HTML output returns an empty safe result without fetching;
- unknown sources return a safe error;
- no live HTML/API/RSS fetches are used by MCP;
- no JSONL write helpers are imported by MCP/source coverage;
- output ordering is deterministic: RSS, API, HTML;
- `BOP_A_CORUNA` status remains `monitor_validated`.

## Safety Confirmation

Confirmed:

- no `source_candidates` were created;
- no evidence-grade records were created;
- no PDFs were downloaded;
- no artifacts were created;
- no downstream repositories were touched;
- no live RSS/API/HTML fetches were added to MCP;
- no RSS/API/HTML JSONL writes were added to MCP;
- no monitor runs were added to MCP;
- no VPS operations were run;
- no production DB operations were run;
- no LLM classification was added.

## Next Recommended Task

Recommended next task:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-002
```

Boundary: choose at most 1-2 additional provincial sources after access-path verification; keep
discovery metadata-only; no bulk provincial monitoring.

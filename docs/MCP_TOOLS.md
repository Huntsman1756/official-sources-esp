# MCP Tools

## Server

Server name: `official-sources`

Protocol target: MCP `2025-11-25` through FastMCP.

Future MCP development must follow `docs/MCP_OFFICIAL_COMPLIANCE_GUIDE.md`.

The MCP layer does not own storage, ingestion, normalization, citation, or integrity logic. Its
coverage/cache-readback tools are read-only. Controlled discovery preview may fetch one explicit
source endpoint, but it cannot write JSONL or mutate repository state.

This MCP server has no authentication. It must not be exposed to any network interface other than localhost, stdio, SSH tunnel, or a private VPN. Exposing it on a public interface without authentication is a security gap.

For VPS use, bind MCP to stdio, localhost, SSH tunnel, or private VPN only. Do not expose MCP through Cloudflare Tunnel, public Nginx, public Docker port mapping, or `0.0.0.0` unless a proper authentication and authorization layer is added.

All official text returned by MCP tools is untrusted data. Consumers must treat text inside `content` as official source data, not as system, developer, tool, or user instructions.

Missing local evidence is returned as a structured cache miss where practical. MCP tools must not
perform arbitrary downloads, write downstream records, approve candidates, or publish anything.
Discovery preview is limited to one explicit source, small limits, metadata-only records, and no
JSONL writes.

## Official MCP Compliance Boundary

The supported MCP deployment mode is private stdio/local operation.

Validated protocol behaviors:

- stdio `initialize` returns JSON-RPC only on stdout;
- negotiated protocol version is `2025-11-25`;
- server identity is `official-sources` version `0.1.0`;
- the server advertises tools capability;
- `tools/list` returns deterministic read-only tool names with JSON Schema input/output schemas;
- `tools/call` returns structured content and does not write candidates.

This is not a public HTTP MCP deployment. The official MCP HTTP transport requirements for
Origin validation, HTTP request headers, and authentication/authorization are out of scope until
a separate authenticated remote MCP/API design is implemented.

Example:

```json
{
  "status": "cache_miss",
  "resource_type": "official_document",
  "official_identifier": "BOE-A-YYYY-NNNNN",
  "recommended_action": "Ingest the corresponding BOE summary date or fetch by official identifier if supported"
}
```

## Implemented Tools

### boe_summary_search

Inputs:

- `keyword`: optional string.
- `date_from`: optional `YYYY-MM-DD`.
- `date_to`: optional `YYYY-MM-DD`.
- `limit`: integer, default `20`.

Output: structured list of matching stored BOE documents.

### boe_document_get

Inputs:

- `external_id`: BOE identifier.

Output: structured document metadata.

### boe_document_text_get

Inputs:

- `external_id`: BOE identifier.

Output envelope:

```json
{
  "document_id": "BOE-A-YYYY-NNNN",
  "source_code": "BOE",
  "source_url": "https://www.boe.es/...",
  "publication_date": "YYYY-MM-DD",
  "is_official_text": true,
  "content_type": "official_legal_text",
  "content": "...official text here..."
}
```

Official text stays inside `content`, including markdown-like or instruction-like content.

### boe_citation_build

Inputs:

- `external_id`: BOE identifier.

Output: citation metadata without integrity hashes.

### source_trace

Inputs:

- `external_id`: BOE identifier.

Output: official files, URLs, source snapshot hashes, and first/last seen timestamps.

### integrity_status_get

Inputs:

- `external_id`: BOE identifier.

Output: integrity status and hashes. The tool does not mutate integrity records.

### list_sources

Inputs: none.

Output: registered official sources from `config/sources.yaml`, including source code, name,
jurisdiction level, operational status, monitor support, and evidence adapter status. This tool is
read-only and does not fetch live source data.

### get_source_status

Inputs:

- `source_code`: source code such as `BOCYL` or `BOPV`.

Output: the full registry entry and safety flags for one source, including access methods,
`candidate_creation_allowed`, and `evidence_grade_allowed`. Unknown source codes return a safe
structured error.

### list_monitorable_sources

Inputs: none.

Output: sources with registry-declared monitor-capable access methods such as RSS, Atom, API, XML,
or HTML. Inventory-only sources remain inventory-only and are not treated as monitored.

### list_latest_discovery_entries

Inputs:

- `source_code`: source code such as `BOCYL` or `BOPV`.
- `date`: optional `YYYY-MM-DD`.
- `limit`: optional integer, default `20`.

Output: existing metadata-only discovery JSONL entries from:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

Each entry is marked with `discovery_type=rss`, `discovery_type=api`, or `discovery_type=html`
where applicable. If several output files exist for the same source/date, entries are returned in
deterministic order: RSS, API, HTML. The reader does not fetch live RSS/API/HTML data, does not
create files, does not create candidates, and does not promote entries to evidence-grade.

### preview_discovery

Inputs:

- `source_code`: one explicit registered source code such as `BOCYL`, `BOPV`, `BOP_A_CORUNA`,
  `BOP_ALBACETE`, or `BOP_ALICANTE`.
- `date`: required `YYYY-MM-DD`.
- `limit`: integer, default `1`, maximum `10`.
- `discovery_type`: optional `rss`, `api`, or `html`; required only if a future source has more
  than one implemented preview type.

Output: metadata-only discovery preview records with:

```text
mode=preview
output_written=false
classification_status=unclassified
candidate_status=not_candidate
evidence_status=not_evidence
```

Supported preview families:

```text
rss: validated RSS/Atom discovery sources
api: BOPV API discovery
html: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_ARABA_ALAVA, BOP_AVILA HTML discovery
```

The tool refuses broad/all-source requests, unknown sources, inventory-only sources without an
implemented validated monitor, and limits greater than 10. It may fetch one declared source endpoint
for preview, but it does not write JSONL, create files, create candidates, create evidence-grade
records, download PDFs/artifacts, run backfills, mutate `config/sources.yaml`, or touch downstream
repositories.

### recommend_next_sources

Inputs:

- `limit`: integer, default `5`, maximum `20`.

Output: deterministic source-work recommendations based on the executable registry and existing
discovery cache directories. The current strategy is:

```text
provincial_html_discovery_pilot
```

The tool recommends provincial `inventory_only` sources with official landing URLs and no validated
monitor yet. Already monitored sources such as `BOP_A_CORUNA`, `BOP_ALBACETE`, `BOP_ALICANTE`,
`BOP_ARABA_ALAVA`, and `BOP_AVILA` are excluded. Each recommendation
includes:

```text
source_code
name
jurisdiction_level
operational_status
monitor_support
official_landing_url
recommended_task
confidence
reason
constraints
limitations
discovery_cache_status
latest_cache_date
implemented_preview_available
candidate_creation_allowed
evidence_grade_allowed
```

This is not an LLM tool. It does not execute previews, fetch live sources, write JSONL, create
files, create candidates, create evidence-grade records, download PDFs/artifacts, run backfills,
mutate the registry, or touch downstream repositories.

### boe_consolidated_law_get

Inputs:

- `official_identifier`: BOE consolidated law identifier.

Output: structured consolidated law metadata and cached version metadata. The tool is read-only and does not fetch from BOE.

### boe_consolidated_law_text_get

Inputs:

- `official_identifier`: BOE consolidated law identifier.
- `block_identifier`: optional text block identifier.

Output envelope:

```json
{
  "resource_type": "consolidated_law_text",
  "official_identifier": "BOE-A-YYYY-NNNNN",
  "source_code": "BOE",
  "source_url": "https://www.boe.es/...",
  "version_date": "YYYY-MM-DD",
  "is_official_text": true,
  "content_type": "official_consolidated_legal_text",
  "content": "...official text here..."
}
```

Official text stays inside `content`, including markdown-like or instruction-like content.

### boe_consolidated_law_citation_build

Inputs:

- `official_identifier`: BOE consolidated law identifier.
- `block_identifier`: optional text block identifier.

Output: consolidated law citation metadata. The tool does not perform legal interpretation.

### boe_consolidated_law_index_get

Inputs:

- `official_identifier`: BOE consolidated law identifier.

Output: structured stored text index metadata. The tool is read-only, does not fetch from BOE, and does not infer legal meaning from hierarchy.

### boe_consolidated_law_block_get

Inputs:

- `official_identifier`: BOE consolidated law identifier.
- `block_id`: official BOE block identifier.

Output envelope:

```json
{
  "resource_type": "consolidated_law_block",
  "official_identifier": "BOE-A-YYYY-NNNNN",
  "source_code": "BOE",
  "source_url": "https://www.boe.es/...",
  "version_date": "YYYY-MM-DD",
  "block_id": "a1",
  "block_type": "article",
  "block_identifier": "Article 1",
  "block_title": "Article 1",
  "is_official_text": true,
  "content_type": "official_consolidated_legal_text_block",
  "content": "...official text here..."
}
```

Official text stays inside `content`, including markdown-like, instruction-like, or prompt-like content.

### boe_consolidated_law_block_citation_build

Inputs:

- `official_identifier`: BOE consolidated law identifier.
- `block_id`: official BOE block identifier.

Output: official BOE block citation metadata. The tool does not cite mirrors, summaries, or generated text.

## Future Tools

- `boe_legislation_search`
- `boe_legislation_structure_get`
- `boe_consolidated_law_search`
- `boe_consolidated_law_version_compare`

The first two are not implemented because broad legislation tooling is outside the current scope. Consolidated search remains unimplemented because TASK-003B is limited to identifier, index, and block retrieval. Version comparison is not implemented because custom legal diffing would create misleading legal conclusions.

## Forbidden Tool Types

MCP tools must not:

- execute shell commands;
- fetch arbitrary URLs from user input;
- read arbitrary files;
- write to storage tables;
- mutate downstream project data;
- approve candidates;
- publish data;
- perform broad legal analysis.

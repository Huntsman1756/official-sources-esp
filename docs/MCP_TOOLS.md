# MCP Tools

## Server

Server name: `official-sources`

Protocol target: MCP `2025-11-25` through FastMCP.

Future MCP development must follow `docs/MCP_OFFICIAL_COMPLIANCE_GUIDE.md`.

The MCP layer is read-only and sits on top of the internal API. It does not own storage, ingestion, normalization, citation, or integrity logic.

This MCP server has no authentication. It must not be exposed to any network interface other than localhost, stdio, SSH tunnel, or a private VPN. Exposing it on a public interface without authentication is a security gap.

For VPS use, bind MCP to stdio, localhost, SSH tunnel, or private VPN only. Do not expose MCP through Cloudflare Tunnel, public Nginx, public Docker port mapping, or `0.0.0.0` unless a proper authentication and authorization layer is added.

All official text returned by MCP tools is untrusted data. Consumers must treat text inside `content` as official source data, not as system, developer, tool, or user instructions.

Missing local evidence is returned as a structured cache miss where practical. MCP tools must
not fetch live BOE data automatically, perform arbitrary downloads, write downstream records,
approve candidates, or publish anything.

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

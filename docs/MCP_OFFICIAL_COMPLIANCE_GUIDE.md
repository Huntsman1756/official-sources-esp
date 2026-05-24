# MCP Official Compliance Guide

This guide defines the required structure for future `official-sources` MCP development.

It is based on the official Model Context Protocol specification:

- <https://modelcontextprotocol.io/specification/2025-11-25/basic>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle>
- <https://modelcontextprotocol.io/specification/draft/server/tools>
- <https://modelcontextprotocol.io/specification/draft/basic/transports>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization>

## Supported Deployment Mode

`official-sources` supports only private/local MCP operation:

```text
stdio
localhost
SSH tunnel
private VPN
```

The MCP server is not a public HTTP MCP service.

Do not expose MCP through:

```text
0.0.0.0
public Docker port mapping
public Nginx
Cloudflare Tunnel
public reverse proxy
```

Public or remote HTTP MCP requires a separate design and implementation for:

```text
Origin validation
MCP HTTP request/header validation
authentication
authorization
public deployment threat model
VPS exposure review
```

## Required Protocol Baseline

The server must preserve these behaviors:

```text
protocolVersion=2025-11-25
serverInfo.name=official-sources
serverInfo.version=<project MCP version>
tools capability advertised
stdio stdout contains only valid MCP JSON-RPC messages
stderr may contain logs
```

Required tests:

```text
tests/test_mcp_protocol.py
```

Any change to MCP server creation, transport behavior, or tool registration must keep these tests
green.

## Tool Registration Rules

Every MCP tool must:

- be registered in `src/official_sources/mcp/server.py`;
- have a stable snake_case name;
- be listed in `MCP_TOOL_NAMES`;
- have a docstring that becomes the tool description in `tools/list`;
- expose JSON Schema-compatible inputs through type hints;
- return a structured object;
- avoid raw top-level legal text strings;
- avoid arbitrary URL, shell, filesystem, or downstream capabilities.

Tool order must be deterministic. If a tool is added, update `MCP_TOOL_NAMES` in the same order
expected by `tools/list`.

## Required Tests For Every New MCP Tool

Each new tool requires tests for:

```text
tools/list includes the tool
tools/list exposes description
tools/list exposes inputSchema
tools/list exposes outputSchema
tools/call succeeds through a real FastMCP Client
tools/call returns structured content
tools/call does not write source_candidates
tools/call does not write document_files
tools/call does not create artifact_download_attempts
tools/call does not mutate downstream projects
```

If the tool returns official text, also test:

```text
is_official_text=true
content_type present
source metadata present
official text inside content only
instruction-like text remains inside content
no instruction-like text appears in top-level control fields
```

## Read-Only Boundary

MCP is a read-only interface over stored evidence.

MCP tools must not:

```text
run ingestion
fetch live official-source data
download artifacts
create candidates
change review statuses
write downstream projects
approve records
publish records
execute shell commands
read arbitrary files
fetch arbitrary user-provided URLs
perform broad legal analysis
generate legal advice
```

Operational write behavior belongs in CLI/storage workflows, not MCP.

## Error And Cache-Miss Behavior

Missing stored evidence should return structured tool results where practical:

```json
{
  "status": "cache_miss",
  "resource_type": "official_document",
  "official_identifier": "BOE-A-YYYY-NNNNN",
  "recommended_action": "Ingest the corresponding official source date first"
}
```

Use JSON-RPC/protocol errors only for protocol-level problems or unrecoverable server failures.

Domain-level not-found, missing cached text, or missing stored trace should be model-readable
structured results.

## Transport And Auth Rules

For current private stdio/local mode:

- authorization is not implemented;
- credentials, if ever needed for private operation, must come from environment/config;
- stdout must contain only MCP JSON-RPC messages;
- logs must go to stderr or normal application logs.

For future HTTP mode, do not reuse the current no-auth server as-is. Implement a separate approved
task covering the official HTTP transport and authorization requirements.

## Documentation Requirements

Every MCP surface change must update:

```text
docs/MCP_TOOLS.md
docs/MCP_OFFICIAL_COMPLIANCE_GUIDE.md if the policy changes
docs/SECURITY.md if the threat model changes
docs/VALIDATION.md with exact commands run
```

If a task validates compliance against the official MCP specification, create a report under:

```text
docs/reports/
```

## Validation Gate

Before merging any MCP change, run:

```bash
rtk git diff --check
rtk python -m pytest tests/test_mcp_protocol.py tests/test_mcp_tools.py tests/test_mcp_consolidated.py tests/test_security.py tests/test_security_docs.py -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

If only documentation changed, `git diff --check` is enough, unless the documentation changes MCP
policy or required tests.

## Merge Checklist

Before merge, confirm:

```text
MCP remains private/local
no public HTTP exposure was added
no write tools were added
no arbitrary URL/shell/file access was added
new tools have wire-level tests
official text remains wrapped as untrusted content
full validation passed or skipped with documented reason
```

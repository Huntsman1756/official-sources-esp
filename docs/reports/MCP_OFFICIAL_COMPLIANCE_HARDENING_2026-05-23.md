# MCP official compliance hardening - 2026-05-23

## Objective

Stabilize the `official-sources` MCP surface against the official Model Context Protocol
requirements before expanding source coverage further.

Official references checked:

- <https://modelcontextprotocol.io/specification/2025-11-25/basic>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle>
- <https://modelcontextprotocol.io/specification/draft/server/tools>
- <https://modelcontextprotocol.io/specification/draft/basic/transports>
- <https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization>

## Scope

This task did not add new source adapters, run backfills, create candidates, download artifacts,
write downstream projects, expose MCP, or touch the VPS.

## Changes

- Added wire-level MCP tests using a real FastMCP client.
- Added a stdio initialization smoke test that verifies stdout contains only JSON-RPC.
- Set the MCP server identity to `official-sources` version `0.1.0`.
- Added explicit MCP server instructions describing the read-only trust boundary.
- Added descriptions for all MCP tools so `tools/list` is discoverable.
- Made the MCP-created SQLite connection usable across FastMCP worker threads.
- Converted `MCP_TOOL_NAMES` to a deterministic ordered tuple.
- Documented the official compliance boundary in `docs/MCP_TOOLS.md`.

## Validated MCP Behaviors

```text
initialize protocolVersion=2025-11-25
serverInfo.name=official-sources
serverInfo.version=0.1.0
tools capability advertised
tools/list deterministic
tools/list includes inputSchema and outputSchema for every tool
tools/list includes descriptions for every tool
tools/call returns structured cache_miss content
tools/call does not create source_candidates
stdio initialize writes JSON-RPC only to stdout
```

## Security Boundary

The project is compliant only for the intended private/local MCP mode:

```text
stdio
localhost
SSH tunnel
private VPN
```

The project is not claiming public HTTP MCP compliance. Public HTTP exposure remains blocked until
a separate design implements and tests:

```text
Origin validation
HTTP MCP request header validation
authentication and authorization
public deployment threat model
```

## Validation

```text
rtk python -m pip install -e .
rtk python -m pytest tests/test_mcp_protocol.py -q
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
Editable install completed; FastMCP 3.3.1 installed for protocol smoke tests.
tests/test_mcp_protocol.py: 4 passed
git diff --check: passed
pytest: 416 passed, 1 warning
ruff check: passed
ruff format --check: passed
```

Full validation is recorded in `docs/VALIDATION.md`.

## Known Limitations

- MCP remains read-only and BOE-focused.
- No remote/public MCP transport is supported.
- Authorization is intentionally absent for stdio/private operation.
- FastMCP handles the core protocol implementation; this repository now has smoke coverage for the
  negotiated behavior it depends on.

## Next Recommended Task

Keep MCP growth frozen until any new MCP tool is added with:

```text
wire-level tools/list coverage
wire-level tools/call coverage
read-only/no-write assertion
prompt-injection envelope assertion when returning official text
documentation update in docs/MCP_TOOLS.md
```

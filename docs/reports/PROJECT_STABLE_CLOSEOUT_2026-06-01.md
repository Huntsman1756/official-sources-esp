# Project stable closeout - 2026-06-01

Task: `TASK-PROJECT-STABLE-CLOSEOUT-2026-06-01`

## Scope

This closeout validates the current source-coverage and MCP surface after the final provincial
monitor wave and the Almeria ZK monitor.

The closeout does not authorize candidate creation, evidence-grade promotion, PDF/artifact
downloads, broad backfills, downstream writes, publication workflows, public MCP exposure, or new
relay infrastructure.

## Registry State

Source of truth:

```text
config/sources.yaml
```

Current counts:

| status | count |
| --- | ---: |
| `monitor_validated` | 50 |
| `metadata_adapter_validated` | 9 |
| `inventory_only` | 6 |

Safety flags:

```text
registered sources: 65
monitor_support=available: 59
monitor_support=none: 6
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
candidate_creation_allowed true count: 0
evidence_grade_allowed true count: 0
```

Inventory-only sources:

| source | reason | flags |
| --- | --- | --- |
| `DOUE` | no validated project access path yet | none |
| `BOCCE` | no validated project access path yet | none |
| `BOME` | no validated project access path yet | none |
| `BOP_CUENCA` | parser path exists, but project VPS is rejected by the official WAF | `blocked_vps=true`, `pending_relay=true` |
| `BOP_SALAMANCA` | parser path exists, but project VPS cannot complete the official fetch reliably | `blocked_vps=true`, `pending_relay=true` |
| `BOP_ZARAGOZA` | parser path exists, but project VPS times out against the official endpoint | `blocked_vps=true`, `pending_relay=true` |

Relay decision:

```text
REL-001 remains backlog-only.
No Cloudflare Worker, Lambda, proxy, tunnel, or residential relay is deployed for the three blocked
provincial sources until a concrete downstream need justifies the maintenance cost.
```

## MCP Validation

VPS in-process FastMCP validation returned:

```text
tools_count 29
tools_match True
preview BOE ok 1 None not_candidate not_evidence
preview BOPV ok 1 2026/05/1813 not_candidate not_evidence
preview BOP_CADIZ ok 1 128.091 not_candidate not_evidence
preview BOP_ALMERIA ok 1 1488-2026 not_candidate not_evidence
blocked_preview not_monitorable True True inventory_only none False False
```

The representative sample covers:

- BOE;
- an autonomous/API source through `BOPV`;
- a provincial HTML source through `BOP_CADIZ`;
- the ZK/XSP provincial case through `BOP_ALMERIA`;
- an inventory-only blocked source through `BOP_ZARAGOZA`.

The `inventory_only` response is explicit: it returns `not_monitorable`, includes
`blocked_vps=true` and `pending_relay=true`, keeps `monitor_support=none`, and keeps both
candidate/evidence permissions false. It does not return an ambiguous empty record set.

MCP stdio smoke on the VPS returned:

```text
initialize official-sources 2025-11-25
tools_list_count 29
first_tool boe_summary_search
```

## VPS Operational State

VPS checks:

```text
db validate: database_path=/opt/official-sources/data/official_sources.sqlite current_version=10 latest_version=10 status=valid
systemctl --failed: 0 loaded units listed
official-sources-boe-daily.timer: loaded enabled active waiting
official-sources-integrity-check.timer: loaded enabled active waiting
official-sources-hermes-auditor.timer: loaded enabled active waiting
official-sources-hermes-scheduled-validation.timer: loaded enabled active elapsed
public listener check: no matching official/mcp/python/uvicorn/fastmcp listener
```

`official-sources-hermes-scheduled-validation.timer` is a completed one-shot validation timer;
`elapsed` is expected and is not a failure.

Deployment alignment:

```text
origin/main: b0c3805
VPS /opt/official-sources/app HEAD: b0c3805
VPS git status --short: clean
previous hot-patch worktree state preserved in stash@{0}: pre-closeout-hotpatch-2026-06-01
editable install refreshed with .venv/bin/python -m pip install -e .
```

Post-fast-forward VPS MCP validation repeated successfully with the same representative sample:

```text
tools_count 29
preview BOE ok 1 None not_candidate not_evidence
preview BOPV ok 1 2026/05/1813 not_candidate not_evidence
preview BOP_CADIZ ok 1 128.091 not_candidate not_evidence
preview BOP_ALMERIA ok 1 1488-2026 not_candidate not_evidence
blocked_preview not_monitorable True True inventory_only none False False
```

Post-fast-forward MCP stdio smoke:

```text
returncode 0
initialize official-sources 2025-11-25
tools_list_count 29
first_tool boe_summary_search
stderr_has_traceback False
```

## Local Validation

Focused validation after the MCP preview fix:

```text
rtk uv run pytest tests/test_mcp_tools.py::test_mcp_preview_discovery_runs_html_preview_without_writing tests/test_mcp_tools.py::test_mcp_preview_discovery_runs_almeria_zk_html_preview_without_writing tests/test_mcp_tools.py::test_mcp_preview_discovery_refuses_inventory_only_unmonitored_source -q
3 passed, 2 warnings

rtk uv run pytest tests/test_mcp_tools.py tests/test_mcp_protocol.py -q
83 passed, 2 warnings

rtk uv run ruff check src tests
All checks passed
```

Full-suite validation:

```text
rtk uv run pytest -q
721 passed, 2 warnings

rtk uv run ruff check src tests
All checks passed

git diff --check
passed
```

## Closeout Decision

Decision:

```text
GO for stable private MCP/source-coverage closeout, with REL-001 deferred.
```

Conditions preserved:

- 59 sources are monitorable or adapter-backed for metadata-only coverage;
- 6 sources are honestly blocked as inventory-only;
- no source can create candidates automatically;
- no source can promote evidence-grade records automatically;
- MCP is private/read-only and returns explicit blocked status for non-monitorable sources;
- relay infrastructure is intentionally deferred until needed.

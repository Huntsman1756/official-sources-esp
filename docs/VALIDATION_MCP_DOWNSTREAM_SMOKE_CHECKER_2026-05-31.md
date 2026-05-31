# Validation - MCP Downstream Smoke Checker

Date: 2026-05-31

Task: `TASK-MCP-DOWNSTREAM-SMOKE-CHECKER-001`

Scope:

```text
read-only in-process MCP smoke checker
current downstream consumers only
no downstream preview/import commands
no shell execution
no monitor previews
no live fetches
no JSONL writes
no candidate creation
no evidence-grade creation
no product automation
```

Expected local validation:

```text
python -m ruff check src/official_sources/source_coverage.py src/official_sources/mcp/tools.py src/official_sources/mcp/server.py tests/test_mcp_tools.py tests/test_mcp_protocol.py
python -m ruff format --check src/official_sources/source_coverage.py src/official_sources/mcp/tools.py src/official_sources/mcp/server.py tests/test_mcp_tools.py tests/test_mcp_protocol.py
python -m pytest tests/test_mcp_tools.py tests/test_mcp_protocol.py -q
python -m pytest -q
git diff --check
```

Required checker behavior:

```text
check_downstream_integration_smokes returns one result for each current consumer
supported consumers: oposiciones2.0, eduayudas, la-ayuda, renta-verificable
consumer alias renta resolves to renta-verificable
unknown consumers return structured unsupported_consumer
all smoke calls are hardcoded in-process official-sources functions
no downstream_preview_command is executed
no monitor preview is executed
no live fetch is executed
no JSONL is written
no registry mutation is performed
```

Required safety result:

```text
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
downstream_commands_executed=false
monitor_previews_executed=false
live_fetches_performed=false
jsonl_written=false
registry_mutated=false
```

Observed result:

```text
focused MCP/security tests: 79 passed, 1 warning
full suite: 598 passed, 1 warning
ruff check focused files: passed
ruff format --check focused files: passed
git diff --check: passed
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
data/rss_monitor: absent
data/html_monitor: absent
markdown fences: balanced
tool smoke: ok downstream_integration_smoke_run 4 4 0
downstream_commands_executed=false
monitor_previews_executed=false
live_fetches_performed=false
jsonl_written=false
registry_mutated=false
```

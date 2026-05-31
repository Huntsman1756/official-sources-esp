# Validation - MCP Downstream Integration Closure

Date: 2026-05-31

Task: `TASK-MCP-DOWNSTREAM-INTEGRATION-CLOSURE-001`

Scope:

```text
read-only downstream integration smoke matrix
current consumers only
no downstream writes
no candidate creation
no evidence-grade creation
no live fetches
no product automation
```

Local validation:

```text
python -m ruff check src/official_sources/source_coverage.py src/official_sources/mcp/tools.py src/official_sources/mcp/server.py tests/test_mcp_tools.py tests/test_mcp_protocol.py
python -m ruff format --check src/official_sources/source_coverage.py src/official_sources/mcp/tools.py src/official_sources/mcp/server.py tests/test_mcp_tools.py tests/test_mcp_protocol.py
python -m pytest tests/test_mcp_tools.py tests/test_mcp_protocol.py -q
python -m pytest -q
git diff --check
```

Expected safety checks:

```text
rg -c "candidate_creation_allowed: false" config/sources.yaml
rg -c "evidence_grade_allowed: false" config/sources.yaml
Test-Path data/rss_monitor
Test-Path data/html_monitor
```

Required result:

```text
candidate_creation_allowed=false for 65/65
evidence_grade_allowed=false for 65/65
data/rss_monitor absent
data/html_monitor absent
BOP_ALICANTE remains degraded/manual-review
```

Observed result:

```text
focused MCP tests: 72 passed, 1 warning
focused MCP/consolidated tests: 80 passed, 1 warning
full suite: 593 passed, 1 warning
ruff check focused files: passed
ruff format --check focused files: passed
git diff --check: passed
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
data/rss_monitor: absent
data/html_monitor: absent
markdown fences: balanced
tool smoke: ok downstream_integration_smoke_matrix 4
```

The new tool is validated through:

```text
tests/test_mcp_tools.py
tests/test_mcp_protocol.py
```

It must return read-only profiles for:

```text
oposiciones2.0
eduayudas
la-ayuda
renta-verificable
```

It must not:

```text
run downstream preview/import commands
run discovery previews
write JSONL
mutate config/sources.yaml
create candidates
create evidence-grade records
publish product content
send notifications
touch downstream repositories
```

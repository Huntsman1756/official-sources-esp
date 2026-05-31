# Validation: MCP Fiscal Reference Planner

Date: 2026-05-31

Task: `TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001`

Validation commands:

```text
python -m pytest tests/test_mcp_tools.py tests/test_mcp_protocol.py -q
python -m ruff check src/official_sources/downstream_planners.py src/official_sources/source_coverage.py src/official_sources/mcp/tools.py src/official_sources/mcp/server.py tests/test_mcp_tools.py tests/test_mcp_protocol.py
python -m ruff format --check src/official_sources/downstream_planners.py src/official_sources/source_coverage.py src/official_sources/mcp/tools.py src/official_sources/mcp/server.py tests/test_mcp_tools.py tests/test_mcp_protocol.py
git diff --check
python -m pytest -q
```

Safety assertions:

```text
resolve_fiscal_reference returns manual_review_required
exact_reference_resolved=false
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
```

Out of scope:

```text
tax advice
deduction applicability
legal meaning
fiscal claim verification
downstream writes
candidate creation
evidence-grade promotion
artifact downloads
live source fetches
```

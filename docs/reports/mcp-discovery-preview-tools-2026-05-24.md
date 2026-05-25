# MCP discovery preview tools

Task: `TASK-MCP-DISCOVERY-PREVIEW-001`

Date: 2026-05-24

## Summary

The MCP source coverage surface now includes a controlled discovery preview tool:

```text
preview_discovery
```

The tool may execute one-source metadata-only discovery previews for implemented monitor families:

```text
rss: validated RSS/Atom discovery sources
api: BOPV API discovery
html: BOP_A_CORUNA HTML discovery
```

This adds controlled autonomy to the MCP without creating a write path.

## Limits

`preview_discovery` requires:

- one explicit `source_code`;
- one `date`;
- `limit` between 1 and 10;
- implemented validated monitor support for the selected discovery type.

The default limit is 1. If exactly one implemented preview type exists for the source, the tool
infers `discovery_type`. If future sources expose more than one implemented preview type, callers
must pass `discovery_type` explicitly.

## Refusal Rules

The tool refuses:

- broad selectors such as `ALL` or `*`;
- unknown source codes;
- `limit > 10`;
- invalid discovery types;
- inventory-only sources without implemented validated monitor support;
- a requested discovery type that is not implemented for the source.

## Output Contract

Successful results return:

```text
resource_type=discovery_preview
mode=preview
output_written=false
discovery_only=true
```

Records remain metadata-only:

```text
classification_status=unclassified
candidate_status=not_candidate
evidence_status=not_evidence
```

## What Was Not Done

This task did not:

- write RSS/API/HTML JSONL;
- create files;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- mutate `config/sources.yaml`;
- promote registry status;
- run backfills;
- touch downstream repositories;
- run VPS operations;
- run production DB operations;
- add LLM classification.

## Validation

Targeted MCP tests were first written and verified red because `preview_discovery` was absent. After
implementation:

```text
python -m pytest tests/test_mcp_tools.py -q
35 passed, 1 warning
```

Final validation:

```text
python -m pytest tests/test_mcp_tools.py tests/test_mcp_protocol.py -q
40 passed, 1 warning

python -m ruff check src tests
All checks passed!

python -m pytest -q
522 passed, 1 warning

git diff --check
OK
```

Source-tree CLI sanity:

```text
BOCYL: operational_status=metadata_adapter_validated monitor_support=available
BOPV: operational_status=metadata_adapter_validated monitor_support=available
BOP_A_CORUNA: operational_status=monitor_validated monitor_support=available
```

## Next Recommended Task

`TASK-MCP-COVERAGE-RECOMMENDATIONS-001` can use registry state, cache presence, and safe preview
results to recommend the next source work without writing candidates/evidence or running broad
monitors.

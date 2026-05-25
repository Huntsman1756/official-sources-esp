# MCP coverage recommendations

Task: `TASK-MCP-COVERAGE-RECOMMENDATIONS-001`

Date: 2026-05-24

## Summary

The MCP now exposes:

```text
recommend_next_sources
```

This tool provides deterministic recommendations for next source work from registry and cache state.
It does not use LLM classification and does not run monitors.

## Current Strategy

The initial strategy is:

```text
provincial_html_discovery_pilot
```

Selection rules:

- source is `jurisdiction_level=provincial`;
- source is `operational_status=inventory_only`;
- source has `monitor_support=none`;
- source has an official landing URL;
- `candidate_creation_allowed=false`;
- `evidence_grade_allowed=false`.

Already monitored sources such as `BOP_A_CORUNA` are excluded.

## Recommendation Fields

Each recommendation includes:

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

The tool checks existing discovery cache directories for the source and reports:

```text
discovery_cache_status=has_discovery_cache | no_discovery_cache
latest_cache_date=<YYYY-MM-DD> | null
```

## Safety Boundaries

The tool does not:

- execute previews;
- fetch live RSS/API/HTML sources;
- write RSS/API/HTML JSONL;
- create files;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- mutate `config/sources.yaml`;
- run backfills;
- touch downstream repositories;
- run VPS operations;
- run production DB operations;
- add LLM classification.

Recommendations are planning signals only. A human-reviewed implementation task is still required
before validating a new monitor.

## Validation

Targeted tests were first written and verified red because `recommend_next_sources` was absent.
After implementation:

```text
python -m pytest tests/test_mcp_tools.py -q
41 passed, 1 warning
```

Final validation:

```text
python -m pytest tests/test_mcp_tools.py tests/test_mcp_protocol.py -q
45 passed, 1 warning

python -m ruff check src tests
All checks passed!

python -m pytest -q
527 passed, 1 warning

git diff --check
OK
```

Source-tree sanity:

```text
tools.recommend_next_sources(limit=3)
status=ok
strategy=provincial_html_discovery_pilot
recommendations=BOP_ALBACETE,BOP_ALICANTE,BOP_ALMERIA
```

## Next Recommended Task

Use `recommend_next_sources` output to choose at most two provincial sources for:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-002
```

The follow-up task must stay metadata-only, preview-first, and without candidates, evidence-grade
records, PDFs/artifacts, backfills, or downstream writes.

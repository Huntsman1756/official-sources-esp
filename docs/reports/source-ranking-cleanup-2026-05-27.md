# Source Ranking Cleanup

Date: 2026-05-27

Task: `TASK-MCP-SOURCE-RANKING-CLEANUP-001`

## Decision

`recommend_next_sources` remains a read-only planning aid, but its normal ranking no longer treats
documented blocked or deferred provincial sources as ordinary next candidates.

`BOP_ALMERIA` remains in the executable registry as `inventory_only` with `monitor_support=none`.
It is not monitored, not removed from inventory, and not marked as validated. It is excluded from
the normal recommendation ranking because the documented provincial discovery evaluation found a
ZK/JavaScript surface that needs a separate endpoint-specific or JS-capable audit.

## Current Normal Ranking

The normal provincial HTML discovery ranking now prioritizes the previously documented waves before
alphabetical fallback:

```text
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
BOP_SEVILLA
BOP_ZARAGOZA
```

Already monitored provincial sources remain excluded:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_LUGO
```

## Scope

Changed:

- `src/official_sources/source_coverage.py`
- `tests/test_mcp_tools.py`
- `docs/MCP_TOOLS.md`
- `PROJECT_STATE.md`
- `TASK_QUEUE.md`

Not changed:

- `config/sources.yaml`
- provincial monitor implementations
- RSS/API/HTML monitor write paths
- VPS checkout
- Hermes configuration
- BOE timer
- integrity timer
- systemd units
- downstream repositories

## Safety

The MCP recommendation tool still does not fetch live sources, execute previews, write JSONL,
create files, create candidates, create evidence-grade records, download PDFs/artifacts, run
backfills, mutate the source registry, touch downstream repositories, or touch VPS/prod DB state.

## Validation

Targeted red/green test cycle:

```text
rtk python -m pytest tests/test_mcp_tools.py -q
```

Initial red result after updating tests:

```text
3 failed, 39 passed
```

Green result after implementation:

```text
42 passed, 1 warning
```

The remaining warning is the pre-existing Starlette `python_multipart` deprecation warning from the
test environment.

## Next Task

Open a separate task for `TASK-PROVINCIAL-READONLY-BATCH-AUDIT-001`.

That task should perform a read-only batch audit of remaining provincial `inventory_only` sources
without adding monitors or changing registry statuses. Classify access-path evidence first, then
choose a small set of metadata-only pilots by evidence rather than alphabetical order.

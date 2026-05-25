# CLI entrypoint consistency - 2026-05-24

Task: `TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001`

## Scope

This is a development validation consistency task. It does not change source coverage semantics,
registry values, monitor behavior, ingestion behavior, candidates, evidence, artifacts, backfills,
downstream writes, VPS operations, production DB operations, or LLM classification.

## Issue

During `TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001`, the installed global console script:

```bash
official-sources
```

showed stale pre-RSS-003 registry state for:

```text
BOIB
BOC_CANTABRIA
DOE
```

The current source tree correctly showed those sources as:

```text
operational_status=monitor_validated
monitor_support=available
```

The stale script path observed in this environment was:

```text
C:\Users\rome_\AppData\Local\Programs\Python\Python312\Scripts\official-sources.exe
```

## Resolution

The source-tree module entrypoint now executes the CLI directly:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOIB
```

This command is the recommended validation path when the installed console script may be stale.

The local console script can be refreshed with an editable install from the repository root:

```bash
python -m pip install -e ".[dev]"
```

Editable install was not run by this task; no global environment mutation was required.

## Documentation Updated

Updated:

- `README.md`
- `docs/SOURCE_COVERAGE_USAGE.md`
- `PROJECT_STATE.md`
- `TASK_QUEUE.md`

## Validation

Source-tree CLI sanity:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOIB
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOC_CANTABRIA
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source DOE
```

Expected source-tree status:

```text
BOIB: operational_status=monitor_validated monitor_support=available
BOC_CANTABRIA: operational_status=monitor_validated monitor_support=available
DOE: operational_status=monitor_validated monitor_support=available
```

Code validation:

```bash
git diff --check
python -m ruff check src tests
python -m pytest -q
```

Validation results:

```text
git diff --check: OK
python -m ruff check src tests: OK
python -m pytest -q: 495 passed, 1 warning
```

## Guardrail Confirmation

This task did not create:

- `source_candidates`;
- evidence-grade records;
- PDFs;
- artifact files;
- downstream product writes;
- backfills;
- RSS JSONL writes;
- API JSONL writes;
- all-source runs;
- VPS operations;
- production DB operations;
- LLM classification.

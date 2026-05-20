# Platform Cleanup

Date: 2026-05-20

## Scope

`TASK-PLATFORM-002` performed a small cleanup pass after the BOE, BOJA, EduAyudas, and `la-ayuda`
pilots.

This was not a source-expansion task. No backfills, candidate creation, artifact downloads,
downstream writes, MCP exposure, RAG work, or database schema changes were performed.

## Files Changed

- `src/official_sources/cli.py`
- `tests/test_cli.py`
- `docs/SOURCES_POLICY.md`
- `docs/DOWNSTREAM_ONBOARDING.md`
- `docs/DOWNSTREAM_IMPORT_CHECKLIST.md`
- `docs/reports/PLATFORM_CLEANUP_2026-05-20.md`

## Alias Added

Added the generic preferred CLI command:

```bash
official-sources find-source-candidates
```

It uses the same source-aware candidate finder as the existing command and supports:

- `--source BOE`
- `--source BOJA`
- `--profile la-ayuda`
- `--profile boja-ayudas`
- `--dry-run`
- `--no-write`
- `--write`
- `--limit`

The generic command is intended for new source families and cross-source operational docs.

## Backwards Compatibility

The existing command remains available:

```bash
official-sources find-boe-candidates
```

It remains BOE-default and source-aware, including the existing `--source BOJA` behavior.

The help text now describes it as a legacy/BOE-default compatible path and recommends
`find-source-candidates` for new usage.

## Checklist Added

Added:

```text
docs/DOWNSTREAM_IMPORT_CHECKLIST.md
```

The checklist covers:

- preview first;
- write evidence only;
- preserve citation and integrity fields;
- block integrity warnings;
- create downstream candidates only after evidence staging;
- create drafts only after review;
- never publish on import;
- keep downstream-specific publication rules outside `official-sources`.

`docs/DOWNSTREAM_ONBOARDING.md` now links to the checklist.

## Validation

Executed:

```bash
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: OK
rtk python -m pytest -q: 248 passed
rtk python -m ruff check .: OK
rtk python -m ruff format --check .: OK
```

## Next Recommended Task

Recommended next task:

```text
TASK-PLATFORM-003 - Downstream import path cleanup for EduAyudas
```

Reason:

EduAyudas has already validated local/dev ingestion, but a cleaner REST/local import path would
reduce reliance on direct SQL rehearsal steps before adding more source families.

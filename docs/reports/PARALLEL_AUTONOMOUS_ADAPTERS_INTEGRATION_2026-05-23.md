# Parallel Autonomous Adapters Integration - 2026-05-23

## Scope

Integrated four parallel metadata-only autonomous bulletin adapter MVP branches:

- `agent/bopv-mvp`
- `agent/boa-mvp`
- `agent/dogc-mvp`
- `agent/borm-mvp`

The integration preserved the operational boundary for this phase:

- no VPS ingestion
- no backfills
- no candidate creation
- no artifact downloads
- no downstream writes
- no MCP exposure

## Branch Review

Each branch was reviewed with:

```bash
git diff --stat main..origin/<branch>
git diff --check main..origin/<branch>
git log --oneline main..origin/<branch>
git diff --name-status main..origin/<branch>
```

Review result:

| Branch | Result | Notes |
| --- | --- | --- |
| `agent/bopv-mvp` | clean | BOPV/EHAA metadata adapter, fixtures, tests and report only |
| `agent/boa-mvp` | clean | BOA metadata adapter, fixtures, tests and report only |
| `agent/dogc-mvp` | clean | DOGC metadata adapter, fixtures, tests and report only |
| `agent/borm-mvp` | clean | BORM metadata adapter, fixtures, tests and report only |

No branch contained DB files, artifact payloads, logs, env files, downstream project changes, candidate writes or VPS scripts.

## Merge Result

Merge order:

1. `agent/bopv-mvp`
2. `agent/boa-mvp`
3. `agent/dogc-mvp`
4. `agent/borm-mvp`

Conflicts:

- `src/official_sources/cli.py`
- `src/official_sources/storage/repository.py`

Conflict resolution:

- kept all four source-specific CLI commands:
  - `ingest-bopv-date`
  - `ingest-boa-date`
  - `ingest-dogc-date`
  - `ingest-borm-date`
- kept each source's validation, ingestion runner and optional test fetcher wiring;
- kept each `ensure_official_source_*` method as an independent source registration;
- did not collapse source logic into a generic adapter during integration.

Integrated code commit:

```text
c418213
```

## Adapter MVPs Integrated

| Source | CLI command | Metadata strategy | Artifact policy |
| --- | --- | --- | --- |
| BOPV/EHAA | `official-sources ingest-bopv-date --date YYYY-MM-DD` | calendar/date discovery plus official issue XML | URLs preserved only |
| BOA | `official-sources ingest-boa-date --date YYYY-MM-DD` | official JSON query by publication date | URLs preserved only |
| DOGC | `official-sources ingest-dogc-date --date YYYY-MM-DD` | official API date search and document metadata | URLs preserved only |
| BORM | `official-sources ingest-borm-date --date YYYY-MM-DD` | official XML index by publication date | URLs preserved only |

All four MVPs are metadata-only and create `ingestion_runs` plus official document metadata. They do not download PDFs/XML/HTML as artifacts and do not create candidates.

## Validation

Local validation after conflict resolution:

```text
git diff --check: ok
rtk python -m pytest -q: 411 passed
rtk python -m ruff check .: ok
rtk python -m ruff format --check .: ok
```

Focused merge validation before full suite:

```text
tests/test_cli_bopv.py
tests/test_cli_boa.py
tests/test_cli_dogc.py
tests/test_cli_borm.py
tests/test_bopv_adapter.py
tests/test_boa_adapter.py
tests/test_dogc_adapter.py
tests/test_borm_adapter.py

Result: 60 passed
```

CLI smoke:

```text
official-sources --help: ok
official-sources ingest-bopv-date --help: ok
official-sources ingest-boa-date --help: ok
official-sources ingest-dogc-date --help: ok
official-sources ingest-borm-date --help: ok
```

## VPS Deploy

Deployment was performed only after local validation passed.

Command class:

```text
git pull --ff-only origin main
python -m pip install -e .
official-sources --help
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

VPS result:

```text
deployed_commit=c418213
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

Operational safety:

- no ingestion run was executed on VPS;
- no backfill was executed;
- no candidates were created;
- no artifacts were downloaded;
- no downstream write was executed.

Note: `pip install -e .` emitted the existing warning `Ignoring invalid distribution ~fficial-sources`, but the install command completed successfully and the CLI/DB validation checks passed.

## Files Changed

Major integrated areas:

- `src/official_sources/sources/bopv/`
- `src/official_sources/sources/boa/`
- `src/official_sources/sources/dogc/`
- `src/official_sources/sources/borm/`
- `src/official_sources/cli.py`
- `src/official_sources/storage/repository.py`
- source-specific adapter and CLI tests
- source-specific minimal fixtures
- source-specific local MVP reports

## Branch Cleanup

Safe to delete after this report is pushed and no follow-up review is pending:

- `agent/bopv-mvp`
- `agent/boa-mvp`
- `agent/dogc-mvp`
- `agent/borm-mvp`

## Recommended Next Operational Task

Do not run four backfills in parallel.

Recommended serial next task:

```text
TASK-AUTO-BOPV-003 - Controlled BOPV/EHAA 30-day metadata backfill
```

Reason:

- BOPV/EHAA had a successful local published-date smoke with a realistic document count;
- it uses official XML evidence for metadata;
- it was already a strong alternative candidate after BOCYL;
- it is a good first comparison point against BOCYL before expanding to BOA, DOGC or BORM operations.

Alternative if BOPV shows operational friction:

```text
TASK-AUTO-BORM-003 - Controlled BORM 30-day metadata backfill
```

BORM also had a clean local smoke, but its current-index strategy should be checked carefully before wider historical use.

# Parallel Agents Integration Report - 2026-05-21

## Scope

Integrated four isolated agent branches into `main` and deployed the resulting safe CLI/code changes
to the project VPS.

No data ingestion was run. No backfills were run. No candidates were created. No downstream projects
were touched. No MCP exposure was changed.

## Branches Reviewed

| branch | commit | review result |
| --- | --- | --- |
| `origin/agent/official-registry` | `fc7fc90` | Documentation-only registry update; scope accepted. |
| `origin/agent/bdns-candidate-profiles` | `6e91a2c` | Documentation and deterministic YAML example only; scope accepted. |
| `origin/agent/bdns-hardening` | `306e50e` | BDNS parser/ingestion/CLI diagnostics and tests only; scope accepted. |
| `origin/agent/source-cli-alias` | `7902ab9` | Candidate CLI alias/help/tests/docs only; scope accepted. |

## Merge Order

1. `origin/agent/official-registry`
2. `origin/agent/bdns-candidate-profiles`
3. `origin/agent/bdns-hardening`
4. `origin/agent/source-cli-alias`

`origin/agent/official-registry` fast-forwarded from the starting `main`.
The remaining branches merged with normal merge commits.

## Conflicts

No manual conflicts.

`src/official_sources/cli.py` was auto-merged cleanly when integrating
`origin/agent/source-cli-alias` after `origin/agent/bdns-hardening`.

## Validation

Local validation after all merges:

```text
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Results:

```text
git diff --check: passed
pytest: 314 passed
ruff check: passed
ruff format --check: 85 files already formatted
```

CLI smoke checks:

```text
rtk official-sources --help
rtk official-sources find-source-candidates --help
rtk official-sources find-boe-candidates --help
rtk official-sources ingest-bdns-latest --help
```

The installed console script was not available on the local PATH, so the equivalent local package
invocation was used:

```text
PYTHONPATH=src rtk python -m official_sources.cli --help
PYTHONPATH=src rtk python -m official_sources.cli find-source-candidates --help
PYTHONPATH=src rtk python -m official_sources.cli find-boe-candidates --help
PYTHONPATH=src rtk python -m official_sources.cli ingest-bdns-latest --help
```

All four smoke checks exited with code `0`.

## Deploy Decision

Deployed to VPS because:

- code changed in `src/official_sources/cli.py`;
- code changed in the BDNS adapter;
- full local validation passed;
- changes are safe for the deployed CLI;
- no ingestion/backfill/candidate command was required.

## VPS Result

VPS used:

```text
mcpspain-official-sources-vps
```

Command shape:

```text
cd /opt/official-sources/app
git pull --ff-only origin main
. .venv/bin/activate
python -m pip install -e .
official-sources --help
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Result:

```text
git pull: fast-forwarded to 4f5247836304225f76e2ae5b41ddf248ed41b322
editable install: succeeded
official-sources --help: passed
db validate: database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

Operational note:

```text
pip emitted warnings about an invalid old distribution named ~fficial-sources in the VPS venv.
The warning did not block install, CLI help, or database validation.
```

## Final Integrated Commit

The deployed integration commit before this report:

```text
4f5247836304225f76e2ae5b41ddf248ed41b322
```

## Branch Cleanup

Safe to delete after confirming no follow-up review is needed:

```text
agent/official-registry
agent/bdns-candidate-profiles
agent/bdns-hardening
agent/source-cli-alias
```

## Recommended Next Task

Run a constrained DOGV candidate dry-run next, using `find-source-candidates`, before any write-mode
candidate creation.

BDNS should remain high priority, but the next BDNS step should be a controlled local dry-run/profile
test path before creating real candidates or scheduling VPS ingestion.

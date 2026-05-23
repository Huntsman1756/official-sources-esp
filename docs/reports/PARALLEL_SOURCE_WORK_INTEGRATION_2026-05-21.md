# Parallel Source Work Integration - 2026-05-21

## Scope

This report records the supervisor integration of four local parallel branches
and one controlled VPS operation.

Critical constraints applied:

- branches were reviewed before merge;
- no branch was blindly merged;
- only one VPS operation was executed;
- BDNS and BOCYL operations were not combined;
- no artifacts were downloaded;
- no downstream project was touched;
- no MCP surface was exposed.

## Branches Reviewed

| branch | commit | scope | review result |
| --- | --- | --- | --- |
| `agent/bopv-audit` | `9cbc645` | BOPV/EHAA endpoint discovery plus small `ROADMAP.md` update | accepted |
| `agent/platform-docs-cleanup` | `40ca86b` | next-phase planning report | accepted |
| `agent/bdns-local-ingestion-prep` | `48bcb47` | BDNS local temp-DB preflight report | accepted |
| `agent/bocyl-candidate-prep` | `88b135a` | BOCYL candidate batch preflight report | accepted |

Review commands used for each branch:

```bash
git fetch origin
git diff --stat main..origin/<branch>
git diff --check main..origin/<branch>
git log --oneline main..origin/<branch>
```

Scope checks:

```text
forbidden_files=none observed
generated_artifacts=none observed
db_backups_logs_env=none observed
downstream_repo_changes=none observed
```

## Branches Merged

Merge order:

```text
1. agent/bopv-audit
2. agent/platform-docs-cleanup
3. agent/bdns-local-ingestion-prep
4. agent/bocyl-candidate-prep
```

Conflicts:

```text
none
```

Integrated main after merge:

```text
commit=d8b90f0
push_status=success
```

## Files Integrated

Reports added:

```text
docs/reports/BOPV_ENDPOINT_FIXTURE_DISCOVERY_2026-05-21.md
docs/reports/OFFICIAL_SOURCES_NEXT_PHASE_PLAN_2026-05-21.md
docs/reports/BDNS_LATEST_INGESTION_PREFLIGHT_2026-05-21.md
docs/reports/BOCYL_CANDIDATE_BATCH_PREFLIGHT_2026-05-21.md
```

Shared doc updated:

```text
docs/ROADMAP.md
```

The `ROADMAP.md` change only points BOPV/EHAA to the new endpoint discovery
report.

## Validation

Local validation on integrated `main`:

```text
git diff --check=passed
rtk python -m pytest -q=345 passed
rtk python -m ruff check .=passed
rtk python -m ruff format --check .=passed
cli_help=passed
```

CLI help smoke covered:

```text
official_sources.cli --help
official_sources.cli find-source-candidates --help
official_sources.cli ingest-bdns-latest --help
official_sources.cli ingest-bocyl-date --help
```

## Deploy

VPS deploy:

```text
host=157.90.22.40
path=/opt/official-sources/app
deployed_commit=d8b90f0
deploy_status=success
db_validate_before_operation=valid
```

The integrated branch was mostly documentation. Deploy was still performed so
the VPS worktree matched `main` before the approved operation.

## VPS Operation

Chosen operation:

```text
BOCYL-005 candidate batch
```

Reason:

```text
BOCYL preflight was clean, the profile was already validated, and the operation
was limited to 21 metadata-only candidates.
```

BDNS-003 was not run in this pass.

Operational report:

```text
docs/reports/BOCYL_30_DAY_CANDIDATE_BATCH_2026-05-21.md
```

Summary:

| metric | value |
| --- | ---: |
| documents scanned | 773 |
| matches total before filters | 435 |
| matches after filters | 21 |
| candidates created | 21 |
| BOCYL candidates before | 0 |
| BOCYL candidates after | 21 |
| total source_candidates before | 125 |
| total source_candidates after | 146 |
| artifact_download_attempts before | 442 |
| artifact_download_attempts after | 442 |
| artifact directory size before | 30M |
| artifact directory size after | 30M |

DB and privacy:

```text
db_validate_after_operation=valid
mcp_privacy_check=no official/mcp/python/uvicorn/fastmcp listener found
```

Backups:

```text
pre=/opt/official-sources/data/backups/official_sources_before_bocyl_candidate_batch_20260523_120734.sqlite
post=/opt/official-sources/data/backups/official_sources_after_bocyl_candidate_batch_20260523_120825.sqlite
```

## Branches Safe To Delete

After this integration commit is pushed, these branches are safe to delete:

```text
agent/bopv-audit
agent/platform-docs-cleanup
agent/bdns-local-ingestion-prep
agent/bocyl-candidate-prep
```

## Next Recommended Task

```text
TASK-AUTO-BOCYL-006 - Review BOCYL candidate evidence labels
```

Secondary next tasks:

```text
TASK-BDNS-003 - Controlled BDNS latest calls ingestion on VPS
TASK-AUTO-BOPV-002 - BOPV/EHAA metadata adapter MVP
TASK-DOGV-LA-AYUDA-STAGING - Continue DOGV evidence staging review
```

Keep the same execution model:

```text
docs/audits/preflight = parallel local branches
VPS/DB/candidates = one supervisor operation per pass
downstream writes = separate explicit task
```

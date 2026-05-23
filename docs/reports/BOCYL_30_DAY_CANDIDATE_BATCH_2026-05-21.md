# BOCYL 30-Day Candidate Batch - 2026-05-21

## Scope

This report records the first limited BOCYL candidate creation batch over stored
metadata from the 30-day BOCYL window.

Rules applied:

- candidates were created only from stored BOCYL metadata;
- `--write` was used explicitly;
- no PDF/XML/HTML artifacts were downloaded;
- no BOCYL backfill was run;
- no BDNS operation was run in the same pass;
- no EduAyudas work was performed;
- no `la-ayuda` work was performed;
- no downstream writes were performed;
- no MCP surface was exposed;
- no approvals or publications were performed.

## Context

Input metadata window:

```text
source_code=BOCYL
date_range=2026-04-21 -> 2026-05-20
BOCYL official_documents=773
```

Preflight:

```text
docs/reports/BOCYL_CANDIDATE_BATCH_PREFLIGHT_2026-05-21.md
```

Profile refinement baseline:

```text
docs/reports/BOCYL_CANDIDATE_PROFILE_REFINEMENT_2026-05-21.md
documents_scanned=773
matches_total=435
matches_after_filters=21
match_rate=2.72%
```

## Deploy

VPS:

```text
host=157.90.22.40
path=/opt/official-sources/app
deployed_commit=d8b90f0
```

Deploy commands:

```bash
cd /opt/official-sources/app
git pull --ff-only origin main
. .venv/bin/activate
python -m pip install -e .
official-sources --help
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Result:

```text
deploy_status=success
db_validate_before=valid
```

`pip install -e .` emitted existing local warnings about an invalid
`~fficial-sources` distribution in the virtualenv, but the install command,
CLI help, and DB validation completed successfully.

## Backup

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_bocyl_candidate_batch_20260523_120734.sqlite
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_bocyl_candidate_batch_20260523_120825.sqlite
```

## Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOCYL \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile bocyl-ayudas \
  --limit 21 \
  --write
```

## Result

CLI summary:

| metric | value |
| --- | ---: |
| documents scanned | 773 |
| matches total before filters | 435 |
| matches after filters | 21 |
| documents matched | 21 |
| candidates created | 21 |
| excluded by keyword rules | 414 |
| write limit | 21 |

Candidate counts:

| metric | before | after | delta |
| --- | ---: | ---: | ---: |
| total `source_candidates` | 125 | 146 | +21 |
| BOCYL `source_candidates` | 0 | 21 | +21 |

Review status:

```text
review_status_distribution=human_review_required:146
bocyl_review_status_distribution=human_review_required:21
bocyl_project_distribution=generic:21
```

## Safety Checks

| check | before | after |
| --- | ---: | ---: |
| BOCYL official_documents | 773 | 773 |
| artifact_download_attempts | 442 | 442 |
| artifact directory size | 30M | 30M |

Additional checks:

```text
db_validate_after=valid
mcp_privacy_check=no official/mcp/python/uvicorn/fastmcp listener found
```

No artifact growth or artifact download attempts were observed.

## Known Limitations

The BOCYL candidates are metadata keyword matches only. They are not approved,
not published, and not downstream evidence.

The profile is intentionally conservative, but the 21 candidates still require
human review. Some university-program notices may be relevant only for narrow
student groups or may require a later evidence/manual decision.

## Next Recommended Task

```text
TASK-AUTO-BOCYL-006 - Review BOCYL candidate evidence labels
```

Recommended guardrails:

- review the 21 BOCYL candidates manually;
- keep all downstream writes disabled;
- do not download artifacts until a candidate is selected for evidence;
- do not combine with BDNS ingestion in the same operational pass.

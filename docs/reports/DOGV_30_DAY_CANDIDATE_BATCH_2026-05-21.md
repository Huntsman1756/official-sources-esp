# DOGV 30-Day Candidate Batch - 2026-05-21

## Summary

TASK-AUTO-DOGV-005 created the first limited DOGV `source_candidates` batch using the refined
`dogv-ayudas` profile.

The batch was deliberately capped at 25 candidates. All new candidates remain in
`human_review_required`. No artifacts were downloaded. No downstream projects were touched. No DOGV
backfill was run. Nothing was approved or published. MCP exposure was unchanged.

## Deployed Code

```text
deployed_commit=55170eed0002b5569a86aa1e25c4ace147f2cfde
repository=/opt/official-sources/app
database=/opt/official-sources/data/official_sources.sqlite
db_validation_before=current_version=8 latest_version=8 status=valid
```

The VPS checkout was clean before the run.

## Source, Profile, and Limit

```text
source=DOGV
profile=dogv-ayudas
date_from=2026-04-21
date_to=2026-05-20
limit=25
write_mode=write
review_status=human_review_required
```

The previous dry-run for the same range/profile produced:

```text
documents_scanned=1113
matches_total=705
matches_after_filters=76
filtered_match_rate=6.83%
reduction_vs_la_ayuda=73.43%
```

## Pre-Run State

```text
source_candidates_total_before=100
DOGV_source_candidates_before=0
artifact_download_attempts_before=432
artifact_directory_size_before=26M
DOGV_documents_in_range=1113
review_status_distribution_before=human_review_required:100
```

## Backup Before Write

Verified backup created with `db backup --full-check`:

```text
backup_before=/opt/official-sources/data/backups/official_sources_before_dogv_candidate_batch_20260522_154100.sqlite
backup_before_size=53M
backup_before_status=verified
```

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source DOGV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile dogv-ayudas \
  --limit 25 \
  --write
```

The command used stored DOGV metadata only. It did not download PDFs, XML, HTML, or other artifacts.

## Write Result

```text
documents_scanned=1113
matches_total=705
matches_after_filters=76
documents_matched=76
candidates_created=25
candidates_skipped_existing=0
review_status=human_review_required
write_mode=write
write_limit=25
excluded_by_keyword_rules=629
sample_count=25
```

## Post-Run State

```text
source_candidates_total_after=125
DOGV_source_candidates_after=25
DOGV_candidates_created=25
artifact_download_attempts_after=432
artifact_directory_size_after=26M
review_status_distribution_after=human_review_required:125
DOGV_review_status_distribution=human_review_required:25
db_validation_after=current_version=8 latest_version=8 status=valid
```

Expected result was met:

```text
source_candidates: 100 -> 125
DOGV source_candidates: 0 -> 25
new DOGV candidates in human_review_required: 25 / 25
```

## Sample Candidates

| candidate_id | identifier | date | status | note |
| ---: | --- | --- | --- | --- |
| 101 | `DOGV:DOGV-C-2026-16062` | 2026-05-20 | `human_review_required` | Becas de ayuda para estudiar master. |
| 102 | `DOGV:DOGV-C-2026-16067` | 2026-05-20 | `human_review_required` | Becas para practicas externas internacionales. |
| 103 | `DOGV:DOGV-C-2026-16321` | 2026-05-20 | `human_review_required` | Practicas becadas universitarias. |
| 104 | `DOGV:DOGV-C-2026-15641` | 2026-05-19 | `human_review_required` | Beca de iniciacion a la investigacion. |
| 105 | `DOGV:DOGV-C-2026-15642` | 2026-05-19 | `human_review_required` | Beca de iniciacion a la investigacion. |
| 106 | `DOGV:DOGV-C-2026-15801` | 2026-05-19 | `human_review_required` | Ayudas dirigidas a alumnado universitario. |
| 107 | `DOGV:DOGV-C-2026-15376` | 2026-05-18 | `human_review_required` | Possible noise: sports/entity subsidy. |
| 108 | `DOGV:DOGV-C-2026-15504` | 2026-05-18 | `human_review_required` | Ayudas de movilidad para estudiantes. |
| 109 | `DOGV:DOGV-C-2026-15505` | 2026-05-18 | `human_review_required` | Ayudas para estudiantes en movilidad. |
| 110 | `DOGV:DOGV-C-2026-13949` | 2026-05-14 | `human_review_required` | Becas para alumnado universitario. |

The batch intentionally preserves review noise because this is the first real DOGV candidate creation
run and every candidate remains gated by human review.

## Artifact and Downstream Safety

```text
artifact_download_attempts: 432 -> 432
artifact_directory_size: 26M -> 26M
PDF/XML/HTML downloads: none
downstream writes: none
EduAyudas touched: no
la-ayuda touched: no
published: no
approved: no
DOGV backfill run: no
```

## MCP Privacy Check

Command:

```bash
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener reported
```

## Backup After Write

Verified backup created with `db backup --full-check`:

```text
backup_after=/opt/official-sources/data/backups/official_sources_after_dogv_candidate_batch_20260522_154159.sqlite
backup_after_size=53M
backup_after_status=verified
```

## Known Limitations

The first 25 candidates include high-quality student and scholarship matches, but also some expected
review noise such as sports/entity subsidies, employment-related subsidies, and procedural education
items. This is acceptable for a capped first batch because the review status remains
`human_review_required`.

No evidence extraction was performed. Candidate quality should be assessed from metadata first before
any scoped artifact download is considered.

## Recommended Next Task

```text
TASK-AUTO-DOGV-006 - DOGV candidate triage
```

Recommended scope:

```text
source=DOGV
candidate_ids=101..125
mode=metadata_only
no_artifact_downloads=true
no_downstream_writes=true
```

After metadata-only triage, only selected candidates should move to scoped evidence collection.

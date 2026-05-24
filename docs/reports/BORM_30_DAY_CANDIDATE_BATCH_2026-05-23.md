# BORM 30-Day Candidate Batch

Date: 2026-05-24

Task: `TASK-AUTO-BORM-006`

Scope: controlled BORM candidate creation from stored metadata.

No artifacts were downloaded. No downstream project was touched. No approval or publication action was taken.

## Context

Previous calibration report:

```text
docs/reports/BORM_CANDIDATE_PROFILE_CALIBRATION_2026-05-23.md
```

Calibrated dry-run:

```text
source=BORM
profile=borm-ayudas
range=2026-04-21 -> 2026-05-20
documents_scanned=549
matches_total=255
matches_after_filters=13
match_rate=2.37%
candidates_created=0
```

## Deployed State

VPS path:

```text
/opt/official-sources/app
```

Deployed commit:

```text
5d76754
```

Pre-run DB validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## Pre-Run Counts

```text
source_candidates_total=150
BORM source_candidates=0
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
```

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_borm_candidate_batch_20260524_074330.sqlite
```

## Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BORM \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile borm-ayudas \
  --limit 13 \
  --write
```

Command result:

```text
documents_scanned=549
source=BORM
matches_total=255
matches_after_filters=13
documents_matched=13
candidates_created=13
```

## Candidate Result

Post-run counts:

```text
source_candidates_total=163
BORM source_candidates=13
review_status_distribution=human_review_required:13
```

Candidate IDs created:

```text
151
152
153
154
155
156
157
158
159
160
161
162
163
```

Sample candidates:

| candidate_id | external_id | publication_date | review_status |
| --- | --- | --- | --- |
| 151 | `BORM:A-140526-2138` | 2026-05-14 | human_review_required |
| 152 | `BORM:A-130526-2110` | 2026-05-13 | human_review_required |
| 153 | `BORM:A-130526-2111` | 2026-05-13 | human_review_required |
| 154 | `BORM:A-120526-2086` | 2026-05-12 | human_review_required |
| 155 | `BORM:A-110526-2055` | 2026-05-11 | human_review_required |
| 156 | `BORM:A-080526-2009` | 2026-05-08 | human_review_required |
| 157 | `BORM:A-080526-2010` | 2026-05-08 | human_review_required |
| 158 | `BORM:A-080526-2011` | 2026-05-08 | human_review_required |
| 159 | `BORM:A-080526-2012` | 2026-05-08 | human_review_required |
| 160 | `BORM:A-240426-1793` | 2026-04-24 | human_review_required |
| 161 | `BORM:A-230426-1782` | 2026-04-23 | human_review_required |
| 162 | `BORM:A-210426-1745` | 2026-04-21 | human_review_required |
| 163 | `BORM:A-210426-1746` | 2026-04-21 | human_review_required |

## Artifact Safety

```text
artifact_download_attempts=482 -> 482
artifact_bytes=28857411 -> 28857411
artifact_size=30M -> 30M
```

No PDF/XML/HTML artifacts were downloaded.

## Post-Run Validation

DB validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching exposed official/MCP/python/uvicorn/fastmcp listener observed
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_borm_candidate_batch_20260524_074420.sqlite
```

## Known Limitations

- These candidates are metadata-derived only.
- Some BORM titles are truncated in the stored official metadata, so evidence review is needed before downstream routing.
- All candidates remain `human_review_required`.
- No evidence artifacts have been downloaded for these candidates.

## Next Recommended Task

```text
TASK-AUTO-BORM-007 — BORM candidate triage
```

Scope for the next task:

```text
metadata-only
candidate_ids=151,152,153,154,155,156,157,158,159,160,161,162,163
no artifact downloads
no review_status changes
no downstream writes
```

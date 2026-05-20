# BOE 6-Month Candidate Batch - 2026-05-20

## Scope

This report documents a controlled creation of a limited BOE candidate batch from the cached 6-month BOE summary range.

Target range:

```text
2025-11-20 to 2026-05-20
```

Profile:

```text
la-ayuda
```

Creation limit:

```text
50
```

This task did not call BOE, did not run a new summary backfill, did not download XML/HTML/PDF artifacts, did not approve candidates, did not publish anything, and did not write to downstream projects.

## Deployment State

- Deployed commit used for the candidate write: `1734700`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- Pre-run DB validation: valid

## Safety Note

Before candidate creation, the write path was hardened to skip existing candidates for the same `document_id` and `project_key`.

Reason:

- The 6-month dry-run range overlaps the previous 30-day pilot batch.
- The first filtered matches included documents that already had `source_candidates`.
- Creating a new batch without deduplication would have produced duplicate candidates for the same project key.

Validation for the hardening:

```text
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
208 passed
ruff check passed
ruff format --check passed
```

## Pre-Run State

Pre-run database counts:

| Item | Count |
|---|---:|
| `source_candidates` | 25 |
| `source_candidates.human_review_required` | 25 |
| `artifact_download_attempts` | 366 |

Pre-run artifact directory size:

```text
23M
```

## Pre-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_before_6m_candidate_batch_20260520_072315.sqlite
```

Result:

- Status: created successfully
- Size: 43M

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --date-from 2025-11-20 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --limit 50 \
  --write
```

The command exited successfully.

Command summary:

| Metric | Value |
|---|---:|
| Documents scanned | 21,513 |
| Matches total | 2,041 |
| Matches after filters | 372 |
| Documents matched | 372 |
| Candidates created | 50 |
| Existing candidates skipped | 25 |
| Write limit | 50 |

Write mode:

```text
write
```

Review status used for created candidates:

```text
human_review_required
```

## Candidate Creation Result

| Item | Before | After |
|---|---:|---:|
| `source_candidates` | 25 | 75 |
| `source_candidates.human_review_required` | 25 | 75 |
| New candidates | 0 | 50 |

All 50 new candidates have:

```text
review_status=human_review_required
```

No candidates were approved or published.

## New Candidate Sample

Sample from the new rows:

| Candidate ID | Official identifier | Date | Department | Keywords | Score | Review status |
|---:|---|---|---|---|---:|---|
| 26 | `BOE-B-2026-16141` | `2026-05-19` | Foreign affairs/cooperation | `subvenciones`, `convocatoria` | 3 | `human_review_required` |
| 27 | `BOE-B-2026-16157` | `2026-05-19` | Labour/SEPE | `subvenciones`, `convocatoria` | 3 | `human_review_required` |
| 28 | `BOE-B-2026-16158` | `2026-05-19` | Labour/SEPE | `subvenciones`, `convocatoria` | 3 | `human_review_required` |
| 29 | `BOE-B-2026-16159` | `2026-05-19` | Labour/SEPE | `subvenciones`, `convocatoria` | 3 | `human_review_required` |
| 30 | `BOE-B-2026-16236` | `2026-05-19` | Health | `ayudas` | 2 | `human_review_required` |
| 31 | `BOE-B-2026-16237` | `2026-05-19` | Social rights | `subvenciones` | 2 | `human_review_required` |
| 32 | `BOE-B-2026-16238` | `2026-05-19` | Equality | `subvenciones`, `discapacidad` | 4 | `human_review_required` |
| 33 | `BOE-B-2026-16025` | `2026-05-18` | Catalonia | `vivienda` | 2 | `human_review_required` |
| 34 | `BOE-B-2026-14388` | `2026-05-06` | Equality | `subvenciones` | 2 | `human_review_required` |
| 35 | `BOE-B-2026-14177` | `2026-05-05` | Foreign affairs/cooperation | `subvenciones`, `convocatoria` | 3 | `human_review_required` |

The sample remains metadata-only. No raw legal text is included here.

## Selection Notes

- The batch uses the same refined `la-ayuda` profile as the 6-month dry-run.
- The first 25 already-existing candidates for the same project key were skipped.
- The command continued through the filtered match list until it created 50 new candidates.
- The batch intentionally includes noisy or unclear metadata matches; the next task should triage them before evidence downloads.

## Artifact Verification

| Item | Before | After |
|---|---:|---:|
| Artifact directory size | 23M | 23M |
| `artifact_download_attempts` | 366 | 366 |

No artifact download command was run.

## Post-Run Database Validation

Post-run DB validation:

```text
valid
```

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Post-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_after_6m_candidate_batch_20260520_072434.sqlite
```

Result:

- Status: created successfully after DB validation
- Size: 44M

## Known Issues

- This was metadata-only candidate creation; relevance has not been reviewed.
- XML, HTML and PDF evidence artifacts were not downloaded for the new candidates.
- The new batch contains expected noise from generic grants, institutional notices, housing and sector-specific subsidies.
- The previous 6-month summary backfill still has the known `2026-05-20` BOE summary `404` failure; this task did not retry or reinterpret that date.
- Candidate `review_status` intentionally remains `human_review_required`; this is not approval.

## Next Recommended Task

Recommended next task:

```text
TASK-005D - 6-month candidate review triage
```

Do not download XML/HTML/PDF for all 50 immediately. First triage the new candidates into:

```text
likely_relevant
unclear
false_positive
out_of_scope
```

Then select a smaller evidence batch, ideally 10 to 20 candidates, for XML/HTML evidence download.

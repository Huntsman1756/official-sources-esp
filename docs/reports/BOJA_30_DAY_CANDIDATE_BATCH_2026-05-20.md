# BOJA 30-Day Candidate Batch - 2026-05-20

## Summary

TASK-AUTO-005 created the first limited BOJA `source_candidates` batch from stored BOJA metadata.

The batch used the BOJA-specific `boja-ayudas` profile and an explicit write limit of 25 candidates.

No PDFs, XML, or HTML artifacts were downloaded. No downstream projects were touched. No candidates were approved or published.

## Deployed State

VPS application path:

```text
/opt/official-sources/app
```

Deployed commit:

```text
2ab44f0
```

Database status before write:

```text
current_version=8
latest_version=8
status=valid
```

## Source And Profile

```text
source=BOJA
profile=boja-ayudas
date_from=2026-04-21
date_to=2026-05-20
limit=25
```

The profile was previously validated in TASK-AUTO-004B:

```text
documents_scanned=1500
matches_total=372
matches_after_filters=36
filtered_match_rate=2.40%
```

## Pre-Run State

```text
source_candidates_total=75
BOJA source_candidates=0
review_status_distribution=human_review_required:75
artifact_download_attempts=392
artifact_directory_size=24M
BOJA official_documents=1500
```

## Pre-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_before_boja_candidate_batch_20260520_153048.sqlite
size=47M
status=created
```

The backup command used the repository `db backup` command, which creates a readable SQLite backup through the online backup API.

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --source BOJA \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile boja-ayudas \
  --limit 25 \
  --write
```

The command used stored BOJA metadata only. It did not call BOJA live endpoints.

## Write Result

```text
documents_scanned=1500
source=BOJA
matches_total=372
matches_after_filters=36
documents_matched=36
candidates_created=25
candidates_skipped_existing=0
review_status=human_review_required
write_mode=write
write_limit=25
excluded_by_keyword_rules=336
sample_count=25
```

Only the first 25 filtered BOJA matches were written.

## Post-Run State

```text
source_candidates_total=100
BOJA source_candidates=25
new BOJA candidates=25
review_status_distribution=human_review_required:100
BOJA review_status_distribution=human_review_required:25
artifact_download_attempts=392
artifact_directory_size=24M
```

Expected count transition:

```text
source_candidates: 75 -> 100
BOJA source_candidates: 0 -> 25
```

## Sample Candidates

| candidate_id | source | official_identifier | date | matched keywords | score | review_status | note |
| ---: | --- | --- | --- | --- | ---: | --- | --- |
| 76 | BOJA | `BOJA:disposition.2026.95.21` | 2026-05-20 | discapacidad | 2 | human_review_required | Disability-related metadata signal. |
| 77 | BOJA | `BOJA:disposition.2026.95.6` | 2026-05-20 | becas, estudiantes | 4 | human_review_required | Scholarship/student signal. |
| 78 | BOJA | `BOJA:disposition.2026.94.5` | 2026-05-19 | ayudas, estudiantes | 4 | human_review_required | Student aid signal. |
| 79 | BOJA | `BOJA:disposition.2026.93.28` | 2026-05-18 | becas, convocatoria | 3 | human_review_required | Scholarship/call signal. |
| 80 | BOJA | `BOJA:disposition.2026.92.1` | 2026-05-15 | convocatoria, alumnado | 3 | human_review_required | Education/student wording. |
| 81 | BOJA | `BOJA:disposition.2026.92.55` | 2026-05-15 | ayudas, convocatoria, vivienda, alquiler, jovenes | 8 | human_review_required | Young-rent context retained for review. |
| 82 | BOJA | `BOJA:disposition.2026.91.73` | 2026-05-14 | beca, ayuda | 4 | human_review_required | Scholarship/aid wording. |
| 83 | BOJA | `BOJA:disposition.2026.91.74` | 2026-05-14 | beca, ayuda | 4 | human_review_required | Scholarship/aid wording. |
| 84 | BOJA | `BOJA:disposition.2026.91.75` | 2026-05-14 | beca, ayuda | 4 | human_review_required | Scholarship/aid wording. |
| 85 | BOJA | `BOJA:disposition.2026.91.86` | 2026-05-14 | bases reguladoras, discapacidad | 5 | human_review_required | Disability-related rules wording; needs triage. |

Samples are metadata-only and must not be treated as approved or publishable.

## Artifact And Downstream Safety

```text
artifact_directory_size_before=24M
artifact_directory_size_after=24M
artifact_download_attempts_before=392
artifact_download_attempts_after=392
PDF downloads=0
XML/HTML downloads=0
downstream writes=0
approvals=0
publications=0
```

## DB Validation

Post-run validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## MCP Privacy

Listener check:

```text
ss checks for official, mcp, python, uvicorn, and fastmcp returned no matching listeners.
```

No public MCP listener or SQLite exposure was observed.

## Post-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_after_boja_candidate_batch_20260520_153418.sqlite
size=47M
status=created
```

## Known Limitations

- The command is still named `find-boe-candidates`; source filtering supports BOJA, but a future `find-source-candidates` alias would be clearer.
- BOJA candidates are metadata-only. No PDF, XML, or HTML evidence has been downloaded.
- The candidates are not approved. They remain `human_review_required`.
- The batch has not been triaged for relevance.
- Scoped BOJA artifact download by candidate ID is not part of this task.

## Recommendation

Recommended next task:

```text
TASK-AUTO-006 - BOJA candidate triage
```

Triage labels should mirror the BOE workflow:

```text
likely_relevant
unclear
out_of_scope
false_positive
```

Do not download PDFs until triage selects a small evidence batch and BOJA scoped artifact download behavior is explicitly implemented or verified.

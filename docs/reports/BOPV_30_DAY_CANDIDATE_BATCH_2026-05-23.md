# BOPV 30-Day Candidate Batch - 2026-05-23

## Scope

Created a limited BOPV/EHAA source-candidate batch using the calibrated `bopv-ayudas` profile.

This was a controlled candidate creation task.

No artifacts were downloaded. No downstream projects were touched. Nothing was approved or
published. MCP was not exposed.

## Deployed Commit

```text
9557832
```

The VPS was updated to `origin/main` before the operation, the package was reinstalled in the
virtualenv, and the database validated successfully.

## Target

```text
source=BOPV
profile=bopv-ayudas
date_from=2026-04-21
date_to=2026-05-20
limit=4
write_mode=--write
```

## Pre-Run State

```text
source_candidates_total=146
BOPV source_candidates=0
artifact_download_attempts=482
artifact_bytes=28857411
DB validation=status=valid schema_version=8
```

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_bopv_candidate_batch_20260524_043711.sqlite
```

## Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOPV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile bopv-ayudas \
  --limit 4 \
  --write
```

## Result

```text
documents_scanned=489
matches_total=177
matches_after_filters=4
documents_matched=4
candidates_created=4
candidates_skipped_existing=0
review_status=human_review_required
excluded_by_section=0
excluded_by_department=0
excluded_by_keyword_rules=173
```

## Post-Run State

```text
source_candidates_total=150
BOPV source_candidates=4
artifact_download_attempts=482
artifact_bytes=28857411
DB validation=status=valid schema_version=8
```

Review status distribution for BOPV:

```text
human_review_required=4
```

All new BOPV candidates remain `human_review_required`.

## Created Candidates

| Candidate ID | Official identifier | Publication date | Department | Signal |
| ---: | --- | --- | --- | --- |
| 147 | `BOPV:BOPV-2026-05-2602039a` | 2026-05-15 | Departamento de Educacion | FP grant bases / call |
| 148 | `BOPV:BOPV-2026-05-2601909a` | 2026-05-08 | Departamento de Ciencia, Universidades e Innovacion | Research/university aid bases |
| 149 | `BOPV:BOPV-2026-04-2601788a` | 2026-04-30 | Lanbide-Servicio Publico Vasco de Empleo | Disability/employment aid call |
| 150 | `BOPV:BOPV-2026-04-2601716a` | 2026-04-24 | Departamento de Educacion | FP innovation/entrepreneurship grant bases |

Sample score signals:

```text
BOPV:BOPV-2026-05-2602039a -> subvenciones, bases reguladoras, convocatoria, convocatoria de subvenciones, formacion profesional, formacion
BOPV:BOPV-2026-05-2601909a -> ayudas, bases reguladoras, universidades
BOPV:BOPV-2026-04-2601788a -> ayudas, convocatoria, empleo, discapacidad
BOPV:BOPV-2026-04-2601716a -> subvenciones, bases reguladoras, convocatoria, formacion profesional, formacion
```

## Artifact Safety

```text
artifact_download_attempts_before=482
artifact_download_attempts_after=482
artifact_bytes_before=28857411
artifact_bytes_after=28857411
```

No PDF, XML, or HTML artifacts were downloaded.

## MCP Privacy

The listener check returned no matching `official`, `mcp`, `python`, `uvicorn`, or `fastmcp`
listeners.

## Backups

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_bopv_candidate_batch_20260524_043711.sqlite
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_bopv_candidate_batch_20260524_043817.sqlite
```

Both backups completed successfully.

## Known Limitations

- This is a narrow first-pass BOPV batch with only four candidates.
- The calibrated profile remains conservative and may miss additional legitimate BOPV aid notices.
- Candidate records are metadata-only; no XML/HTML/PDF evidence has been downloaded yet.
- No downstream project should consume these candidates until metadata triage and evidence review
  are completed.

## Next Recommended Task

```text
TASK-AUTO-BOPV-006 - BOPV candidate triage
```

Recommended scope:

```text
metadata-only
review candidate IDs 147,148,149,150
do not download artifacts
do not change review_status
classify likely_relevant / unclear / out_of_scope / false_positive
select evidence candidates for a later scoped XML/HTML download
```

# BOE 30-day candidate pilot - 2026-05-17

## Summary

TASK-004C-RUN3 created a small controlled set of real `source_candidates` from the cached
30-day BOE range using the refined `la-ayuda` profile.

This was a candidate creation pilot only. It did not call BOE, download XML/HTML/PDF artifacts,
write to downstream projects, approve candidates, publish anything, use LLMs, or perform legal
classification.

## Environment

- Host: private VPS, public IP redacted.
- Application path: `/opt/official-sources/app`.
- Database path: `/opt/official-sources/data/official_sources.sqlite`.
- Artifact path: `/opt/official-sources/data/artifacts`.
- Date range: `2026-04-18` through `2026-05-17`.
- Profile: `la-ayuda`.
- Deployed commit: `55c5fcc`.
- Schema status: `current_version=6 latest_version=6 pending_migrations=0`.
- SQLite runtime: `journal_mode=wal synchronous=normal`.

## Pre-run Validation

```text
database_status=valid
source_candidates_before=0
artifact_size_before=22M
```

The VPS does not currently have the `sqlite3` CLI installed, so candidate-count checks were
performed with Python's standard `sqlite3` module against the same database.

## Pre-run Backup

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_candidate_pilot_20260517_200934.sqlite
verification=quick_check
source_check=ok
backup_check=ok
pages=2317
size_bytes=9490432
status=success
```

## CLI Safety Check

`find-boe-candidates --help` showed the required safe write controls:

```text
--profile {la-ayuda}
--dry-run
--no-write
--write
--limit LIMIT
```

Write mode is explicit. `--limit` caps created candidates in write mode.

## Candidate Creation Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --date-from 2026-04-18 \
  --date-to 2026-05-17 \
  --profile la-ayuda \
  --limit 25 \
  --write
```

The command uses stored BOE titles and metadata only.

## Candidate Creation Result

```text
documents_scanned=3896
matches_total=313
matches_after_filters=73
candidates_created=25
write_mode=write
write_limit=25
excluded_by_section=38
excluded_by_department=0
excluded_by_keyword_rules=202
```

Candidate count:

```text
before=0
after=25
created=25
```

Review status distribution:

```text
human_review_required:25
```

All created candidates are `human_review_required`.

## Score Distribution

```text
score_2=15
score_3=8
score_4=1
score_6=1
```

Scores are deterministic keyword-match explanations only. They are not approval, ranking,
eligibility, or legal interpretation signals.

## Sample Candidates

Representative created candidates:

| ID | Identifier | Date | Keywords | Score | Department | Summary |
|---:|---|---|---|---:|---|---|
| 1 | BOE-B-2026-15543 | 2026-05-15 | ayudas | 2 | Presidency / Justice | Training grants for young university graduates. |
| 2 | BOE-B-2026-15551 | 2026-05-15 | ayudas | 2 | Culture | Film production project grants. |
| 3 | BOE-B-2026-15552 | 2026-05-15 | ayudas | 2 | Youth and Children | European Solidarity Corps grants. |
| 4 | BOE-B-2026-15495 | 2026-05-14 | subvenciones, convocatoria | 3 | Labour | Employment-office facility renewal grants. |
| 5 | BOE-B-2026-15496 | 2026-05-14 | subvenciones, convocatoria | 3 | Labour | Local employment-project grants. |
| 6 | BOE-B-2026-15525 | 2026-05-14 | subvenciones | 2 | Culture | Municipal public library modernization grants. |
| 10 | BOE-B-2026-15334 | 2026-05-13 | ayudas, subvenciones | 4 | Defence | Social-action grants linked to the Navy. |
| 11 | BOE-B-2026-15350 | 2026-05-13 | ayudas | 2 | Education | Textbook and teaching-material aid. |
| 14 | BOE-B-2026-15228 | 2026-05-12 | subvenciones, convocatoria, convocatoria de subvenciones | 6 | Labour | Employment and training programme grants in Melilla. |
| 18 | BOE-B-2026-14562 | 2026-05-08 | ayudas | 2 | Education | Aid for students with specific educational support needs. |
| 19 | BOE-B-2026-14621 | 2026-05-08 | vivienda | 2 | Catalonia | Public information notice involving housing/territory metadata. |
| 24 | BOE-B-2026-14386 | 2026-05-06 | ayudas, convocatoria | 3 | Science | Innovation programme aid. |

Each candidate stores the linked BOE document ID plus matched metadata including official
identifier, publication date, title, section, department, official URL, matched keywords, score,
score reasons, and profile name.

## Artifact and BOE Call Checks

```text
artifact_size_before=22M
artifact_size_after=22M
```

No artifact download command was run. The candidate command searches local stored BOE titles and
metadata only. No BOE ingestion or fetch command was run during the pilot.

## Post-run Validation

```text
database_status=valid
source_candidates_after=25
review_status_distribution=human_review_required:25
```

## Post-run Backup

```text
backup_path=/opt/official-sources/data/backups/official_sources_after_candidate_pilot_20260517_201015.sqlite
verification=quick_check
source_check=ok
backup_check=ok
pages=2325
size_bytes=9523200
status=success
```

## MCP Privacy Check

`ss -tulpn` showed no MCP/FastMCP/Python/Uvicorn/official-sources listener and no SQLite
exposure. SSH and loopback DNS listeners were present as expected. The public IP is not recorded
in this report.

## Known Limitations

- Candidate matching remains title/metadata-only.
- No XML, HTML, or PDF evidence was downloaded for these candidates.
- No downstream project consumed these rows.
- The candidates are not approved and not publication-ready.
- False positives remain possible, especially broad institutional grants, `vivienda` public
  information notices, and grants outside the intended `la-ayuda` / `EduAyudas` scope.
- The VPS virtual environment still emits a non-blocking pip warning about a leftover temporary
  distribution directory.

## Next Recommended Task

```text
TASK-004C-RUN4 - Review the 25 pilot candidates and select evidence downloads
```

Recommended constraints:

- review only the 25 `human_review_required` candidates;
- mark obvious false positives locally or document the review decision;
- download XML/HTML only for selected candidates;
- keep PDF on-demand for final evidence;
- do not integrate downstream projects until the candidate/evidence review model is confirmed.

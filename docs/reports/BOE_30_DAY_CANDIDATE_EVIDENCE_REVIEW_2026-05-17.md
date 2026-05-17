# BOE 30-day candidate evidence review - 2026-05-17

## Summary

TASK-004C-RUN4 reviewed the 25 pilot `source_candidates` created from the cached 30-day
BOE range and downloaded XML/HTML evidence artifacts only for a selected subset.

This was an evidence workflow pilot only. It did not approve candidates, publish anything, write
to downstream projects, use LLMs, perform legal classification, expose MCP, or download PDFs.

## Environment

- Host: private VPS, public IP redacted.
- Application path: `/opt/official-sources/app`.
- Database path: `/opt/official-sources/data/official_sources.sqlite`.
- Artifact path: `/opt/official-sources/data/artifacts`.
- Date range: `2026-04-18` through `2026-05-17`.
- Profile: `la-ayuda`.
- Deployed commit: `3519c35`.
- Schema status: `current_version=6 latest_version=6 pending_migrations=0`.
- SQLite runtime: `journal_mode=wal synchronous=normal`.

## Pre-run State

```text
database_status=valid
source_candidates=25
review_status_distribution=human_review_required:25
artifact_size_before=22M
```

Candidate rows were inspected with a read-only query. The operational review labels below were
used only for this report and were not written to the database.

## Review Table

| Candidate | Identifier | Date | Department | Title signal | Keywords | Score | Initial review | Reason |
|---:|---|---|---|---|---|---:|---|---|
| 1 | BOE-B-2026-15543 | 2026-05-15 | Presidency / Justice | University graduate training grants | ayudas | 2 | likely_relevant | Training aid signal with reviewable education-adjacent scope. |
| 2 | BOE-B-2026-15551 | 2026-05-15 | Culture | Film production project grants | ayudas | 2 | unclear | Real grants, but sector scope may be outside la-ayuda/EduAyudas. |
| 3 | BOE-B-2026-15552 | 2026-05-15 | Youth and Children | European Solidarity Corps grants | ayudas | 2 | likely_relevant | Youth grant signal worth evidence review. |
| 4 | BOE-B-2026-15495 | 2026-05-14 | Labour | Employment-office facility grants | subvenciones, convocatoria | 3 | unclear | Grant signal exists, but recipient/use may be institutional infrastructure. |
| 5 | BOE-B-2026-15496 | 2026-05-14 | Labour | Local employment-project grants | subvenciones, convocatoria | 3 | unclear | Employment grant signal, but local-corporation recipient scope needs review. |
| 6 | BOE-B-2026-15525 | 2026-05-14 | Culture | Public library modernization grants | subvenciones | 2 | unclear | Real grants, likely institutional rather than direct citizen/student aid. |
| 7 | BOE-B-2026-15527 | 2026-05-14 | Science | Health research platform grants | subvenciones, convocatoria | 3 | unclear | Research grants, likely institutional and not first evidence target. |
| 8 | BOE-B-2026-15528 | 2026-05-14 | Equality | State-level association grants | subvenciones | 2 | unclear | Social grant signal, but not clearly user-facing aid. |
| 9 | BOE-B-2026-15332 | 2026-05-13 | Foreign Affairs | Development cooperation grants | subvenciones, convocatoria | 3 | unclear | Real grants, but outside likely EduAyudas scope. |
| 10 | BOE-B-2026-15334 | 2026-05-13 | Defence | Social-action grants | ayudas, subvenciones | 4 | likely_relevant | Aid and social-action signal, selected for evidence review. |
| 11 | BOE-B-2026-15350 | 2026-05-13 | Education | Textbook and teaching-material aid | ayudas | 2 | likely_relevant | Direct education aid signal. |
| 12 | BOE-B-2026-15414 | 2026-05-13 | Social Rights | Animal-protection grants | subvenciones | 2 | unclear | Real grants, but outside target domain. |
| 13 | BOE-B-2026-15227 | 2026-05-12 | Labour | Employment insertion grants | subvenciones, convocatoria | 3 | unclear | Employment aid signal, but recipient scope needs review. |
| 14 | BOE-B-2026-15228 | 2026-05-12 | Labour | Employment and training grants | subvenciones, convocatoria, convocatoria de subvenciones | 6 | likely_relevant | Training/employment grant signal with high deterministic score. |
| 15 | BOE-B-2026-15261 | 2026-05-12 | Culture | Rural cultural cooperation aid | ayudas | 2 | unclear | Aid signal exists, but not clearly education or household support. |
| 16 | BOE-B-2026-15262 | 2026-05-12 | Health | Public health programme grants | subvenciones | 2 | unclear | Real grants, likely organizational recipient scope. |
| 17 | BOE-B-2026-15263 | 2026-05-12 | Equality | Training scholarships | becas | 2 | likely_relevant | Scholarship/training signal. |
| 18 | BOE-B-2026-14562 | 2026-05-08 | Education | Aid for students with specific support needs | ayudas | 2 | likely_relevant | Direct student support signal. |
| 19 | BOE-B-2026-14621 | 2026-05-08 | Catalonia | Public information notice involving housing metadata | vivienda | 2 | false_positive | Housing keyword appears in an infrastructure/public-information notice. |
| 20 | BOE-B-2026-14487 | 2026-05-07 | Ecological Transition | Climate training scholarships | becas, convocatoria | 3 | likely_relevant | Scholarship/training signal. |
| 21 | BOE-B-2026-14488 | 2026-05-07 | Ecological Transition | Biodiversity training scholarships | becas, convocatoria | 3 | likely_relevant | Scholarship/training signal. |
| 22 | BOE-B-2026-14359 | 2026-05-06 | Ecological Transition | Water-use public information notice involving housing | vivienda | 2 | false_positive | Housing keyword appears in a water-use notice, not an aid call. |
| 23 | BOE-B-2026-14385 | 2026-05-06 | Culture | Cultural heritage project grants | ayudas | 2 | likely_relevant | Aid signal, selected to validate evidence workflow breadth. |
| 24 | BOE-B-2026-14386 | 2026-05-06 | Science | Innovation programme aid | ayudas, convocatoria | 3 | unclear | Real aid signal, but likely institutional innovation scope. |
| 25 | BOE-B-2026-14387 | 2026-05-06 | Equality | Equality and community culture grants | subvenciones | 2 | unclear | Real grant signal, but domain fit needs human review. |

Review counts:

```text
likely_relevant=10
unclear=13
false_positive=2
```

All 25 database rows remained `review_status=human_review_required`.

## Selected Evidence Candidates

The selected subset was limited to 10 candidates:

```text
candidate_ids=1,3,10,11,14,17,18,20,21,23
```

Selection rationale:

- prefer direct aid, scholarship, training, education, student support, youth support, or social
  support signals;
- avoid obvious public information notices;
- avoid downloading artifacts for all 25 pilot candidates;
- keep PDF on-demand for later human-accepted evidence.

## Pre-download Backup

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_candidate_evidence_download_20260517_202030.sqlite
verification=quick_check
source_check=ok
backup_check=ok
pages=2325
size_bytes=9523200
status=success
```

## Scoped Artifact Download

The repository first received `TASK-004C-FIX5`, which adds scoped artifact downloads by candidate
or document ID. The deployed command was:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-boe-artifacts \
  --candidate-ids 1,3,10,11,14,17,18,20,21,23 \
  --types xml,html
```

Result:

```text
selected_documents=10
artifact_types=xml,html
downloaded=20
skipped=0
changed=0
failed=0
retries=0
throttle_events=18
http_status_summary=html:200:10,xml:200:10
```

No PDF download was run.

## Post-download Validation

```text
database_status=valid
artifact_size_before=22M
artifact_size_after=23M
```

## Evidence Availability

For each selected candidate, the local evidence record now has:

- official URL metadata;
- citation metadata;
- XML and HTML artifact records;
- SHA-256 artifact hashes and source snapshot hashes;
- `hashes_match=true` for the downloaded XML/HTML artifacts;
- clean text rows derived from XML/HTML where implemented.

Full legal text was not printed in the report.

## MCP Privacy Check

`ss -tulpn` showed no MCP/FastMCP/Python/Uvicorn/official-sources listener and no SQLite
exposure. SSH and loopback DNS listeners were present as expected. The public IP is not recorded
in this report.

## Post-download Backup

```text
backup_path=/opt/official-sources/data/backups/official_sources_after_candidate_evidence_download_20260517_202050.sqlite
verification=quick_check
source_check=ok
backup_check=ok
pages=2357
size_bytes=9654272
status=success
```

## Known Limitations

- The review labels are operational report labels only and are not authoritative legal or product
  classification.
- Candidate matching is still title/metadata-only.
- The selected evidence artifacts prove XML/HTML availability, not downstream readiness.
- No PDF artifacts were downloaded in this task.
- No downstream project consumed the candidates or evidence.
- The candidates are not approved and not publication-ready.
- False positives remain possible, especially broad institutional grant calls outside the
  intended la-ayuda/EduAyudas scope.
- The VPS virtual environment still emits a non-blocking pip warning about a leftover temporary
  distribution directory.

## Next Recommended Task

```text
TASK-004D - Candidate evidence review model and selected PDF-on-demand policy
```

Recommended constraints:

- keep candidate approval outside `official-sources`;
- define the exact fields la-ayuda/EduAyudas must ingest from evidence records;
- download PDFs only for human-accepted or final citation evidence;
- add review/export commands before any downstream integration;
- do not start TASK-004B until the downstream candidate/evidence model is confirmed.

# BOA Metadata Backfill Catch-up

Date: 2026-06-14
Task: `TASK-OFFICIAL-SOURCES-BOA-METADATA-BACKFILL-CATCHUP-001`

## Scope

Run a bounded BOA upstream catch-up on the `official-sources` VPS for metadata only.

Allowed surface:

- `official_sources`
- `official_documents`
- `ingestion_runs`
- `document_files` with `file_type=raw_api_response`
- SQLite backups and operational logs

Forbidden surface:

- source candidates
- evidence-grade records
- artifact/PDF downloads
- downstream EduBecas writes
- public publication/drafts
- runtime, systemd, timer, cap, or Hermes contract changes

## Runtime Context

VPS:

```text
host=ubuntu-4gb-nbg1-8
app=/opt/official-sources/app
db=/opt/official-sources/data/official_sources.sqlite
head=bdddd07
git_status=## main...origin/main [ahead 2]
worktree=clean
```

The remote checkout was clean. The branch being ahead of `origin/main` was recorded as runtime
context only; no git operation or code change was performed on the VPS.

## Window

The catch-up window was expanded beyond the original 30-day runbook so the confirmed EduBecas BOA
sample date was included explicitly.

```text
date_from=2026-04-21
date_to=2026-06-05
confirmed_sample_date=2026-06-05
```

## Preflight

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=10
latest_version=10
status=valid

official_sources_boa=0
official_documents_boa=0
source_candidates_boa=0
artifact_download_attempts_boa=0
boa_document_files_total=0
boa_document_files_by_type=[]
boa_recent_ingestion_runs=[]
```

## Backups

Both backups completed with `quick_check` verification.

```text
before_backup=/opt/official-sources/backups/boa-catchup/official_sources_before_boa_catchup_20260614T194045Z.sqlite
before_backup_status=success
before_backup_size_bytes=104718336

after_backup=/opt/official-sources/backups/boa-catchup/official_sources_after_boa_catchup_20260614T194045Z.sqlite
after_backup_status=success
after_backup_size_bytes=120336384
```

Operational log:

```text
/opt/official-sources/logs/boa_catchup_20260614T194045Z.log
```

## Backfill Result

```text
runs=46
success_runs=32
no_publication_runs=14
documents_fetched_total=1384
documents_fetched_max_single_day=65
last_http_status_min=200
last_http_status_max=200
max_retry_count=0
max_throttle_triggered=0
db_validate_after=status=valid
```

The parser limit guard did not trip. No day reached the current BOA endpoint page-risk threshold
of `documents_fetched >= 250`.

The confirmed sample issue date was ingested:

```text
target_date=2026-06-05
issue_identifier=106/2026
documents_fetched=39
documents_new=39
retry_count=0
throttle_triggered=0
last_http_status=200
source_snapshot_hash=d30868b40bb76bd2202580a007af58f3d9c611402d210ccfd94ac8376288361f
```

## Post Verification

```text
official_sources_boa=1
official_documents_boa=1384
source_candidates_boa=0
artifact_download_attempts_boa=0
boa_document_files_total=1384
boa_document_files_missing_hash=0
boa_docs_without_raw_api_response_file=0
boa_document_files_by_type=[('raw_api_response', 1384)]
```

The `2026-06-05` comedor-school rows are present in upstream metadata:

```text
BOA:007958917
publication_date=2026-06-05
title=ORDEN ECU/818/2026, de 29 de mayo, por la que se convocan becas que faciliten la utilizacion del servicio de comedor escolar por parte del alumnado de centros docentes sostenidos con fondos publicos de la Comunidad Autonoma de Aragon y las becas de comedor que complementan las becas de comedor escolar durante el periodo estival no lectivo para el curso 2026/2027.

BOA:007958933
publication_date=2026-06-05
title=EXTRACTO de la Orden ECU/818/2026, de 29 mayo, por la que se convocan becas que faciliten la utilizacion del servicio de comedor escolar por parte del alumnado de centros docentes sostenidos con fondos publicos de la Comunidad Autonoma de Aragon y las becas de comedor que complementan las becas de comedor escolar durante el periodo estival no lectivo, para el curso 2026/2027.
```

## Candidate Dry-run

The BOA profile was run in dry-run mode after the metadata catch-up.

```text
command=official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-source-candidates --date-from 2026-04-21 --date-to 2026-06-05 --source BOA --profile boa-ayudas --dry-run --limit 50
documents_scanned=1384
matches_total=833
matches_after_filters=21
documents_matched=21
candidates_created=0
candidates_skipped_existing=0
review_status=human_review_required
write_mode=dry_run
```

High-signal educational samples appeared on `2026-06-05`:

- material curricular for compulsory-stage alumnado;
- comedor escolar becas for `2026/2027`;
- Erasmus and international mobility complementary grants.

The dry-run also surfaced expected non-student or weaker matches, including youth/certamen and
internal training/practice scholarships. Those should be handled by a separate BOA candidate-review
quality loop, not by this metadata-only catch-up.

## URL Mapping Follow-up

The initial post-check looked for the confirmed BOA `MLKOB` value in `url_html`, but BOA stores
document object links in `url_pdf` because the upstream JSON field is `UrlPdf`.

Follow-up verification in `docs/reports/boa-document-url-mapping-2026-06-14.md` confirmed:

```text
boa_documents_total=1384
boa_url_pdf_present=1384
boa_comedor_pdf_sample=1
boa_pdf_missing_but_raw_urlpdf_present=0
```

Therefore the URL mapping is GO for the metadata-only upstream contract. BOA activation still needs
candidate dry-run quality review before any write path is considered.

## Decision

```text
TASK-OFFICIAL-SOURCES-BOA-METADATA-BACKFILL-CATCHUP-001: DONE
Validation: GO for metadata-only upstream catch-up
Activation readiness: PARTIAL, pending BOA candidate dry-run quality review
EduBecas DB writes: 0
source_candidates writes: 0
artifact/PDF downloads: 0
drafts/publications: 0
runtime/systemd/timer changes: 0
```

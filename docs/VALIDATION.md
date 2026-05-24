# Validation

## 2026-05-21 - TASK-AUTO-BOCYL-004 BOCYL candidate dry-run

VPS read-only validation:

```text
deployed_commit=b4f8603
date_range=2026-04-21 -> 2026-05-20
BOCYL_documents_scanned=773
matches_total=334
matches_after_filters=265
match_rate_after_filters=34.28%
source_candidates=125 -> 125
artifact_download_attempts=442 -> 442
artifact_directory_size=30M -> 30M
db_validate_before=valid
db_validate_after=valid
MCP listener check=no matching listener observed
```

The requested CLI command rejected `--source BOCYL` because BOCYL is not yet in the generic
candidate source allowlist. The dry-run was completed with a read-only script reusing the same
internal `la-ayuda` keyword/filter functions over stored BOCYL metadata. No candidates, artifact
downloads, downstream writes, approvals, or publications were performed.

## 2026-05-21 - TASK-AUTO-BOCYL-003 controlled BOCYL 30-day metadata backfill

VPS operational validation:

```text
deployed_commit=a46c34c
date_range=2026-04-21 -> 2026-05-20
dates_processed=30
success=20
no_publication=10
failed=0
documents_fetched=773
documents_new=773
documents_updated=0
max_docs_in_single_day=2026-04-30:56
page_size_limit_hits=none
artifact_directory_size=30M -> 30M
artifact_download_attempts=442 -> 442
source_candidates=125 -> 125
BOCYL_official_documents=0 -> 773
BOCYL_ingestion_runs=0 -> 30
db_validate_before=valid
db_validate_after=valid
MCP listener check=no matching listener observed
```

Verified backups:

```text
before=/opt/official-sources/data/backups/official_sources_before_bocyl_30d_backfill_20260523_092612.sqlite
after=/opt/official-sources/data/backups/official_sources_after_bocyl_30d_backfill_20260523_092845.sqlite
backup_status=success
```

No BOCYL PDF, XML, or HTML artifact downloads, source candidates, downstream writes, approvals, or
publications were performed.

## 2026-05-21 - TASK-AUTO-BOCYL-002 BOCYL metadata adapter MVP

Local validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 343 passed
ruff check: passed
ruff format --check: passed
```

Controlled local live smoke with a temporary SQLite database:

```text
date=2026-05-20
status=success
issue_identifier=94/2026
documents_fetched=42
documents_new=42
documents_updated=0
last_http_status=200

date=2026-05-17
status=no_publication
documents_fetched=0
documents_new=0
documents_updated=0
last_http_status=200

official_documents=42
source_candidates=0
artifact_download_attempts=0
pdf_document_files=0
xml_document_files=0
raw_api_response_document_files=42
```

No BOCYL PDF, XML, or HTML artifact downloads, source candidates, downstream writes, approvals, or
publications were performed.

## 2026-05-21 - TASK-AUTO-DOGV-007B scoped DOGV artifact downloader

Local validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 323 passed
ruff check: passed
ruff format --check: passed
```

Scope:

```text
command=download-source-artifacts
source=DOGV
selection=--candidate-ids only
types=pdf only
url_source=persisted url_pdf only
```

No broad DOGV downloads, downstream writes, approvals, publications, or candidate status changes are
allowed by the new DOGV scoped download path.

## 2026-05-21 - TASK-BDNS-002 BDNS metadata adapter MVP

Local validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 299 passed
ruff check: passed
ruff format --check: passed
```

Controlled local live smoke with a temporary SQLite database:

```text
ingest-bdns-latest --limit 1:
  status=success
  documents_fetched=1
  documents_new=1
  documents_updated=0
  last_http_status=200
  retry_count=0

ingest-bdns-call --num-conv 907364:
  status=success
  official_identifier=BDNS:907364
  documents_fetched=1
  documents_new=0
  documents_updated=1
  last_http_status=200
  retry_count=0

db_validate=valid
```

No BDNS concessions, source candidates, downstream writes, artifact downloads, approvals, or
publications were performed.

## 2026-05-21 - TASK-AUTO-DOGV-003 DOGV 30-day metadata backfill

VPS operational validation:

```text
deployed_commit=7f1f1ec
date_range=2026-04-21 -> 2026-05-20
dates_processed=30
success=21
no_publication=9
failed=0
documents_fetched=1113
documents_new=1113
documents_updated=0
artifact_directory_size=26M -> 26M
artifact_download_attempts=432 -> 432
source_candidates=100 -> 100
DOGV_official_documents=0 -> 1113
DOGV_ingestion_runs=0 -> 30
db_validate_before=valid
db_validate_after=valid
MCP listener check=no matching listener observed
```

Verified backups:

```text
before=/opt/official-sources/data/backups/official_sources_before_dogv_30d_backfill_20260522_054711.sqlite
after=/opt/official-sources/data/backups/official_sources_after_dogv_30d_backfill_20260522_054936.sqlite
backup_status=success
```

No DOGV PDF, XML, or HTML artifact downloads, source candidates, downstream writes, approvals, or
publications were performed.

## 2026-05-21 - TASK-AUTO-DOGV-002 DOGV metadata adapter MVP

Local validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 285 passed
ruff check: passed
ruff format --check: passed
```

Controlled local live smoke with a temporary SQLite database:

```text
date=2026-05-20
status=success
issue_identifier=10366
documents_fetched=49
documents_new=49
documents_updated=0
last_http_status=200
db_validate=valid
```

No DOGV PDFs, candidates, artifact downloads, downstream writes, approvals, or publications were
performed.

## 2026-05-20 - TASK-AUTO-008 BOJA selected candidate evidence review

VPS read-only validation:

```text
deployed_commit=6466f23
selected_candidates=77,78,79,80,81,82,86,87,93,98
selected_count=10
source_code=BOJA for all selected candidates
url_pdf present=10/10
pdf_available=10/10
pdf_hash_present=10/10
decision_distribution=accept_for_downstream_pilot:4,out_of_scope:6,needs_more_evidence:0,false_positive:0,defer:0
accepted_for_downstream_pilot=77,78,80,86
downstream_fit_EduAyudas=77,78,80,86
source_candidates=100
artifact_download_attempts=432
BOJA PDF document_files=10
selected_pdf_files=10
selected_review_status_distribution=human_review_required:10
all_review_status_distribution=human_review_required:100
selected_integrity_warnings=0
artifact_directory_size=26M
db_validate=valid
MCP listener check=no matching listener observed
```

No source candidate status changes, downstream writes, approvals, publications, new artifact
downloads, BOJA live API calls, or new candidates were performed during evidence review.

## 2026-05-20 - TASK-AUTO-007C BOJA selected candidate PDF download

Local code validation after BOJA URL canonicalization fixes:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 246 passed
ruff check: passed
ruff format --check: passed
```

VPS operational validation:

```text
deployed_commit=6466f23
selected_candidates=77,78,79,80,81,82,86,87,93,98
selected_count=10
url_pdf present before download=10/10
initial_download_result=failed HTTP 307 for 10/10 before canonical URL refresh
final_downloaded=10
final_skipped=0
final_failed=0
final_missing_artifact_url=0
final_http_status_summary=pdf:200:10
source_candidates_before=100
source_candidates_after=100
selected_review_status_distribution=human_review_required:10
all_review_status_distribution=human_review_required:100
artifact_download_attempts_before=402
artifact_download_attempts_after=432
BOJA PDF document_files_before=0
BOJA PDF document_files_after=10
artifact_directory_size_before=24M
artifact_directory_size_after=26M
selected_integrity_warnings=0
db_validate=valid
MCP listener check=no matching listener observed
pre_run_backup=created
post_run_backup=created
```

## 2026-05-20 - TASK-AUTO-007B BOJA evidence URL enrichment

Local code validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 246 passed
ruff check: passed
ruff format --check: passed
```

VPS operational validation:

```text
deployed_commit=1eb9070
selected_candidates=77,78,79,80,81,82,86,87,93,98
selected_count=10
source_code=BOJA for all selected candidates
pre_enrichment_selected_with_url_pdf=0
enrichment_selected_documents=10
enriched=10
skipped=0
failed=0
missing_evidence_url=0
http_status_summary=200:10
selected_with_url_pdf_after=10
url_html_after=0/10
source_candidates_before=100
source_candidates_after=100
selected_review_status_distribution=human_review_required:10
all_review_status_distribution=human_review_required:100
artifact_download_attempts_before=402
artifact_download_attempts_after=402
BOJA PDF document_files_before=0
BOJA PDF document_files_after=0
artifact_directory_size_before=24M
artifact_directory_size_after=24M
db_validate=valid
MCP listener check=no matching listener observed
pre_run_backup=created
post_run_backup=created
PDFs downloaded=0
```

## 2026-05-20 - TASK-AUTO-007 BOJA selected candidate evidence download

Local code validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 242 passed
ruff check: passed
ruff format --check: passed
```

VPS operational validation:

```text
deployed_commit=cbebb84
selected_candidates=77,78,79,80,81,82,86,87,93,98
selected_count=10
source_code=BOJA for all selected candidates
selected_review_status_distribution=human_review_required:10
url_pdf/publicUrl/pathPdf present=0/10
artifact_types_requested=pdf
downloaded=0
skipped=10
failed=0
missing_artifact_url=10
artifact_download_attempts_before=392
artifact_download_attempts_after=402
BOJA PDF document_files_before=0
BOJA PDF document_files_after=0
artifact_directory_size_before=24M
artifact_directory_size_after=24M
db_validate=valid
MCP listener check=no matching listener observed
pre_run_backup=created
post_run_backup=created
```

## 2026-05-20 - TASK-AUTO-006 BOJA candidate triage

VPS read-only validation:

```text
operational_deployed_commit=2ab44f0
BOJA candidates reviewed=25
candidate_ids=76-100
triage_distribution=likely_relevant:9, unclear:10, out_of_scope:1, false_positive:5
selected_evidence_candidates=77,78,79,80,81,82,86,87,93,98
source_candidates_total=100
BOJA source_candidates=25
review_status_distribution=human_review_required:100
BOJA review_status_distribution=human_review_required:25
artifact_download_attempts=392
artifact_directory_size=24M
db_validate=valid
MCP listener check=no matching listener observed
```

## 2026-05-20 - TASK-AUTO-005 BOJA candidate batch

VPS operational validation:

```text
deployed_commit=2ab44f0
source=BOJA
profile=boja-ayudas
date_from=2026-04-21
date_to=2026-05-20
limit=25
write_mode=write
db_validate_before=valid
pre_run_backup=created
source_candidates_before=75
BOJA source_candidates_before=0
candidates_created=25
candidates_skipped_existing=0
source_candidates_after=100
BOJA source_candidates_after=25
review_status_distribution=human_review_required:100
artifact_download_attempts_before=392
artifact_download_attempts_after=392
artifact_directory_size_before=24M
artifact_directory_size_after=24M
db_validate_after=valid
MCP listener check=no matching listener observed
post_run_backup=created
```

## 2026-05-20 - TASK-AUTO-004B BOJA candidate profile refinement

Local validation:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 237 passed
ruff check: passed
ruff format --check: passed
```

VPS dry-run validation:

```text
deployed_commit=3123763
source=BOJA
date_from=2026-04-21
date_to=2026-05-20
profile=boja-ayudas
documents_scanned=1500
matches_total=372
matches_after_filters=36
filtered_match_rate=2.40%
source_candidates=75
artifact_download_attempts=392
artifact_directory_size=24M
db_validate=valid
MCP listener check=no matching listener observed
```

## Commands Executed

TASK-AUTO-004 BOJA candidate dry-run:

```bash
rtk python -m pytest tests/test_cli.py::test_find_boe_candidates_source_filter_supports_boja_dry_run tests/test_cli.py::test_find_boe_candidates_default_source_remains_boe tests/test_cli.py::test_find_boe_candidates_help_contains_false_positive_warning -q
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
ssh mcpspain-official-sources-vps "git fetch origin && git checkout main && git pull --ff-only origin main"
ssh mcpspain-official-sources-vps "python -m pip install -e ."
ssh mcpspain-official-sources-vps "official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
ssh mcpspain-official-sources-vps "official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-boe-candidates --source BOJA --date-from 2026-04-21 --date-to 2026-05-20 --profile la-ayuda --dry-run --limit 200"
ssh mcpspain-official-sources-vps "du -sh /opt/official-sources/data/artifacts"
ssh mcpspain-official-sources-vps "ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true"
```

Result:

- Source-aware dry-run support was added before the VPS dry-run.
- Source-aware focused tests: `3 passed`.
- Full tests after code change: `233 passed`.
- Lint: `All checks passed!`.
- Formatting: `65 files already formatted`.
- VPS deployed commit after fast-forward: `7e84235`.
- BOJA coverage before dry-run: `official_documents=1500`, latest range status `success=21 no_publication=9 failed=0`.
- Dry-run command used stored BOJA metadata only.
- Dry-run result: `documents_scanned=1500`, `matches_total=376`, `matches_after_filters=217`, `candidates_created=0`.
- Filtered BOJA match rate: `217/1500 = 14.47%`.
- `source_candidates` remained `75`.
- `artifact_download_attempts` remained `392`.
- Artifact directory remained `24M`.
- DB validation after dry-run: `status=valid`.
- MCP privacy check found no matching public listener.
- Decision: BOJA needs a source-specific profile before real candidate creation.
- No BOJA API calls, backfills, PDFs, HTML/XML artifacts, candidates, downstream writes, approvals, publications, MCP exposure, RAG, or legal interpretation were run during the dry-run.

TASK-AUTO-003C resumed BOJA 30-day metadata backfill:

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && git fetch origin && git checkout main && git pull --ff-only origin main"
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && . /opt/official-sources/app/.venv/bin/activate && python -m pip install -e ."
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_boja_resume_$(date -u +%Y%m%d_%H%M%S).sqlite"
ssh mcpspain-official-sources-vps "for each date from 2026-04-25 to 2026-05-20: official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-boja-date --date YYYY-MM-DD"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
ssh mcpspain-official-sources-vps "du -sh /opt/official-sources/data/artifacts"
ssh mcpspain-official-sources-vps "ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_after_boja_resume_$(date -u +%Y%m%d_%H%M%S).sqlite"
```

Result:

- VPS deployed commit after fast-forward: `c5d0c01`.
- Pre-resume database validation: `status=valid`.
- Pre-resume BOJA counts: `official_documents=225`, `ingestion_runs=5`.
- Pre-resume artifact state: `artifact_download_attempts=392`, artifact directory `24M`.
- Pre-resume backup: `official_sources_before_boja_resume_20260520_153705.sqlite`, `43.93 MB`, successful.
- Resumed range: `2026-04-25` to `2026-05-20`.
- Resume result: `dates_processed=26`, `success=17`, `no_publication=9`, `failed=0`.
- Resume documents fetched/new/updated: `1275/1275/0`.
- Resume pagination: `pages_fetched_total=17`, `pagination_complete_dates=26`.
- Resume HTTP status distribution: `200=17`, `400 no_publication=9`.
- Original 30-day window final latest status: `success=21`, `no_publication=9`, `failed=0`.
- BOJA documents after resume: `1500`.
- BOJA ingestion runs after resume: `31`; this includes the original failed 2026-04-25 run plus the newer no-publication run.
- Post-resume database validation: `status=valid`.
- Artifact directory remained `24M`; `artifact_download_attempts` remained `392`.
- MCP privacy check found no matching public listener.
- Post-resume backup: `official_sources_after_boja_resume_20260520_153959.sqlite`, `46.69 MB`, successful.
- No PDFs, HTML/XML artifacts, candidates, downstream writes, approvals, publications, BOE tasks, broader BOJA ranges, additional autonomous adapters, MCP exposure, RAG, or legal interpretation were run.

TASK-AUTO-003B BOJA no-publication HTTP behavior hardening:

```bash
rtk python -m pytest tests/test_boja_adapter.py tests/test_cli_boja.py -q
rtk powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path 'G:\tmp\official-sources-boja-400-probe-20260520' | Out-Null; python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-400-probe-20260520\official_sources_boja_400.sqlite' ingest-boja-date --date 2026-04-25; python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-400-probe-20260520\official_sources_boja_400.sqlite' db validate"
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Empirical probe dates: `2026-04-25`, `2026-04-26`, `2026-04-27`, `2026-05-01`, `2026-05-19`.
- Probe result: `2026-04-25`, `2026-04-26`, and `2026-05-01` returned `400 application/json {"status":400,"message":"Bad request"}`.
- Probe result: `2026-04-27` returned `200` with `hits=44 total_hits=44 results=44`.
- Probe result: `2026-05-19` returned `200` with `hits=72 total_hits=72 results=72`.
- Red focused tests failed before implementation because observed BOJA HTTP 400 still mapped to `failed`.
- Focused BOJA/CLI tests after implementation: `23 passed`.
- Live re-test for `2026-04-25`: `status=no_publication pages_fetched=0 pagination_complete=true documents_fetched=0 documents_new=0 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=400`.
- Temporary live re-test database validation: `current_version=8 latest_version=8 status=valid`.
- Full tests: `231 passed`.
- Lint: `All checks passed!`.
- Formatting: `65 files already formatted`.
- Only the exact observed generic BOJA JSON 400 body is classified as `no_publication`; other 400 responses remain failures.
- No BOJA 30-day backfill, candidate extraction, PDF download, downstream write, approval, publication, MCP exposure, RAG, or legal interpretation was run.

TASK-AUTO-003 controlled BOJA 30-day metadata backfill:

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && git fetch origin && git checkout main && git pull --ff-only origin main"
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && . /opt/official-sources/app/.venv/bin/activate && python -m pip install -e ."
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_boja_30d_backfill_$(date -u +%Y%m%d_%H%M%S).sqlite"
ssh mcpspain-official-sources-vps "for each date from 2026-04-21 to 2026-05-20: official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-boja-date --date YYYY-MM-DD"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate"
ssh mcpspain-official-sources-vps "du -sh /opt/official-sources/data/artifacts"
ssh mcpspain-official-sources-vps "ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true"
ssh mcpspain-official-sources-vps "/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_after_boja_30d_backfill_$(date -u +%Y%m%d_%H%M%S).sqlite"
```

Result:

- VPS deployed commit after fast-forward: `d579eda`.
- Pre-run database validation: `status=valid`.
- Pre-run BOJA counts: `official_documents=0`, `ingestion_runs=0`.
- Pre-run artifact state: `artifact_download_attempts=392`, artifact directory `24M`.
- Pre-run backup: `official_sources_before_boja_30d_backfill_20260520_152436.sqlite`, `43.45 MB`, successful.
- Requested range: `2026-04-21` to `2026-05-20`.
- The run stopped on the first failed date: `2026-04-25`.
- Successful dates: `2026-04-21`, `2026-04-22`, `2026-04-23`, `2026-04-24`.
- Failed dates: `2026-04-25`.
- Documents fetched/new/updated before stop: `225/225/0`.
- Pagination for successful dates: `pages_fetched=1`, `pagination_complete=true`.
- Failed date result: `last_http_status=400`, `pagination_complete=false`.
- Post-run database validation: `status=valid`.
- Artifact directory remained `24M`; `artifact_download_attempts` remained `392`.
- MCP privacy check found no matching public listener.
- Post-run backup: `official_sources_after_boja_30d_backfill_20260520_152610.sqlite`, `43.93 MB`, successful.
- No PDFs, HTML/XML artifacts, candidates, downstream writes, approvals, publications, BOE tasks, additional autonomous adapters, MCP exposure, RAG, or legal interpretation were run.
- Next required hardening: define and test BOJA HTTP 400/no-publication behavior before rerunning the 30-day backfill.

TASK-AUTO-002B BOJA pagination completeness guard:

```bash
rtk python -m pytest tests/test_boja_adapter.py tests/test_cli_boja.py -q
rtk powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path 'G:\tmp\official-sources-boja-pagination-smoke-20260520' | Out-Null; python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-pagination-smoke-20260520\official_sources_boja_pagination.sqlite' ingest-boja-date --date 2026-05-19"
rtk powershell -NoProfile -Command "python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-pagination-smoke-20260520\official_sources_boja_pagination.sqlite' db validate"
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Focused BOJA pagination/CLI tests: `18 passed`.
- Live smoke used one BOJA date only, `2026-05-19`, against a temporary local database.
- Live smoke result: `status=success pages_fetched=1 pagination_complete=true documents_fetched=72 documents_new=72 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200`.
- Temporary smoke database validation: `current_version=8 latest_version=8 status=valid`.
- Full tests: `226 passed`.
- Lint: `All checks passed!`.
- Formatting: `65 files already formatted`.
- BOJA pagination now uses `total_hits` as the completeness target.
- Missing pagination metadata or max-page exhaustion fails with `pagination_complete=false`.
- Paginated raw API payloads use a deterministic combined raw hash before parsing.
- No BOJA 30-day backfill, candidate extraction, PDF download, downstream write, approval, publication, MCP exposure, RAG, or legal interpretation was implemented.

TASK-AUTO-002 BOJA adapter MVP:

```bash
rtk python -m pytest tests/test_boja_adapter.py tests/test_cli_boja.py -q
rtk python -m pytest tests/test_boja_adapter.py tests/test_cli_boja.py tests/test_citation.py -q
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:\tmp\official-sources-boja-smoke-20260520\official_sources_boja_smoke.sqlite ingest-boja-date --date 2026-05-19
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:\tmp\official-sources-boja-smoke-20260520\official_sources_boja_smoke.sqlite db validate
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Red focused run failed before implementation because `official_sources.sources.boja` did not exist.
- Focused BOJA tests after implementation: `13 passed`.
- Focused BOJA/citation/CLI regression tests: `16 passed`.
- Live smoke used one BOJA date only, `2026-05-19`, against a temporary local database.
- Live smoke result: `status=success documents_fetched=72 documents_new=72 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200`.
- Temporary smoke database validation: `current_version=8 latest_version=8 status=valid`.
- Full tests: `221 passed`.
- Lint: `All checks passed!`.
- Formatting: `65 files already formatted`.
- BOJA stores metadata only through `ingest-boja-date`.
- BOJA `raw_api_response` file records store `source_snapshot_hash` from raw JSON bytes before parsing.
- BOJA empty `results=[]` responses are recorded as `no_publication`.
- BOJA PDF URLs are preserved as metadata only; no PDF download is performed by the BOJA ingestion command.
- No source candidates, downstream writes, approvals, publications, RAG, or legal interpretation were implemented.

TASK-004C-RUN4 VPS candidate evidence review:

```bash
git pull --ff-only origin main
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_candidate_evidence_download_20260517_202030.sqlite
official-sources --db-path /opt/official-sources/data/official_sources.sqlite --artifact-dir /opt/official-sources/data/artifacts download-boe-artifacts --candidate-ids 1,3,10,11,14,17,18,20,21,23 --types xml,html
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_after_candidate_evidence_download_20260517_202050.sqlite
du -sh /opt/official-sources/data/artifacts
ss -tulpn
```

Result:

- Deployed commit: `3519c35`.
- DB status: `current_version=6 latest_version=6 pending_migrations=0 journal_mode=wal synchronous=normal status=up_to_date`.
- DB validation before and after artifact download: `status=valid`.
- Candidate count: `25`.
- Candidate review labels for the report: `likely_relevant=10 unclear=13 false_positive=2`.
- Selected evidence candidates: `1,3,10,11,14,17,18,20,21,23`.
- Pre-download backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- Scoped artifact download: `selected_documents=10 artifact_types=xml,html downloaded=20 skipped=0 changed=0 failed=0 retries=0 throttle_events=18 http_status_summary=html:200:10,xml:200:10`.
- Artifact directory size before/after: `22M/23M`.
- Post-download backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- MCP privacy check found no MCP/FastMCP/Python/Uvicorn/official-sources listener and no SQLite exposure.
- No PDF download, downstream write, approval, publication, LLM processing, or legal classification was run.
- Tests were not rerun for the report-only commit; TASK-004C-FIX5 code validation was already run before deployment.

TASK-004C-FIX5 local validation:

```bash
rtk python -m pytest tests/test_cli.py::test_download_boe_artifacts_candidate_ids_download_only_selected_documents tests/test_cli.py::test_download_boe_artifacts_document_ids_default_to_xml_html_not_pdf tests/test_cli.py::test_download_boe_artifacts_rejects_mixed_date_and_scoped_selection -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Red focused run failed before implementation because `download-boe-artifacts` did not accept
  `--candidate-ids` or `--document-ids`.
- Focused tests after implementation: `3 passed`.
- Full tests: `199 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- Candidate-scoped artifact download fetches only selected candidate documents.
- Document-scoped artifact download defaults to `xml,html`; PDF is not default.
- `--date` cannot be combined with candidate/document scoped selectors.

TASK-004C-FIX4 local validation:

```bash
rtk python -m pytest tests/test_cli.py::test_find_boe_candidates_normalizes_accents_case_and_whitespace tests/test_cli.py::test_find_boe_candidates_word_boundaries_prevent_bono_carbono tests/test_cli.py::test_find_boe_candidates_phrase_matching_and_scoring_are_explainable tests/test_cli.py::test_find_boe_candidates_profile_excludes_procurement_and_generic_keywords tests/test_cli.py::test_find_boe_candidates_section_and_department_filters_work -q
rtk python -m pytest tests/test_cli.py::test_find_boe_candidates_matches_titles_and_metadata tests/test_cli.py::test_find_boe_candidates_dry_run_does_not_create_candidates tests/test_cli.py::test_find_boe_candidates_no_write_alias_does_not_create_candidates tests/test_cli.py::test_find_boe_candidates_ignores_documents_without_keyword_matches tests/test_cli.py::test_find_boe_candidates_rejects_non_positive_limit tests/test_cli.py::test_find_boe_candidates_does_not_approve_or_publish tests/test_cli.py::test_find_boe_candidates_help_contains_false_positive_warning -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Red focused run failed before implementation because matching was accent-sensitive,
  substring-based, lacked score output, lacked `--profile`, and lacked section/department
  filters.
- Focused refined matching tests after implementation: `5 passed`.
- Existing candidate prefilter regression tests after implementation: `7 passed`.
- Full tests: `194 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- `bono` no longer matches `carbono`.
- Multi-word phrases such as `bases reguladoras` match as phrases.
- The `la-ayuda` profile excludes Section `V-A` by default and filters weak generic-only
  matches such as standalone `convocatoria`.
- Dry-run mode remains no-write and reports deterministic score reasons.

TASK-004C-RUN3 safety precondition local validation:

```bash
rtk python -m pytest tests/test_cli.py::test_find_boe_candidates_matches_titles_and_metadata tests/test_cli.py::test_find_boe_candidates_requires_explicit_write_or_dry_run tests/test_cli.py::test_find_boe_candidates_write_mode_respects_limit tests/test_cli.py::test_find_boe_candidates_help_contains_false_positive_warning -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Red focused run failed before implementation because `--write` did not exist, normal mode still
  wrote candidates, and `--limit` did not cap write-mode creation.
- Focused tests after implementation: `4 passed`.
- Full tests: `196 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- `find-boe-candidates` now requires `--dry-run`, `--no-write`, or explicit `--write`.
- In explicit write mode, `--limit` caps the number of candidates created.
- Written candidates still use `review_status=human_review_required`.

TASK-004C-RUN3 VPS candidate creation pilot:

```bash
git pull --ff-only origin main
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_candidate_pilot_20260517_200934.sqlite
official-sources find-boe-candidates --help
official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-boe-candidates --date-from 2026-04-18 --date-to 2026-05-17 --profile la-ayuda --limit 25 --write
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_after_candidate_pilot_20260517_201015.sqlite
du -sh /opt/official-sources/data/artifacts
ss -tulpn
```

Result:

- Deployed commit: `55c5fcc`.
- DB status: `current_version=6 latest_version=6 pending_migrations=0 journal_mode=wal synchronous=normal status=up_to_date`.
- DB validation before and after candidate creation: `status=valid`.
- Pre-run backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- Candidate count before/after: `0/25`.
- Candidates created: `25`.
- Review status distribution: `human_review_required:25`.
- Artifact directory size before/after: `22M/22M`.
- Post-run backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- MCP privacy check found no MCP/FastMCP/Python/Uvicorn/official-sources listener and no SQLite
  exposure.
- No BOE fetch, artifact download, downstream write, approval, publication, LLM processing, or
  legal classification was run.

TASK-004C-FIX4 VPS refined dry-run:

```bash
git pull --ff-only origin main
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-boe-candidates --date-from 2026-04-18 --date-to 2026-05-17 --profile la-ayuda --dry-run --limit 100
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
du -sh /opt/official-sources/data/artifacts
ss -tulpn
```

Result:

- Deployed commit: `fbdcf42`.
- DB validation before and after dry-run: `current_version=6 latest_version=6 status=valid`.
- Documents scanned: `3896`.
- Refined matches before filters: `313`.
- Refined matches after filters: `73`.
- Baseline matches before refinement: `554`.
- Usable match reduction from baseline: `481` fewer matches, `86.8%`.
- Candidates created: `0`.
- Candidate count before/after: `0/0`.
- Artifact directory size before/after: `22M/22M`.
- Exclusions: `excluded_by_section=38`, `excluded_by_keyword_rules=202`.
- MCP privacy check found no MCP/FastMCP/Python/Uvicorn/official-sources listener and no SQLite
  exposure.
- No BOE API calls, artifact downloads, downstream writes, approval, or publication were run.

TASK-004C-RUN2 VPS candidate prefilter dry-run:

```bash
/opt/official-sources/app/.venv/bin/official-sources find-boe-candidates --help
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
sqlite3 /opt/official-sources/data/official_sources.sqlite "SELECT COUNT(*) FROM source_candidates;"
du -sh /opt/official-sources/data/artifacts
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-boe-candidates --date-from 2026-04-18 --date-to 2026-05-17 --keywords "beca,becas,ayuda,ayudas,subvención,subvenciones,convocatoria,bases reguladoras,educación,estudiantes,alquiler,bono,familia numerosa,discapacidad,transporte,vivienda" --dry-run --limit 100
sqlite3 /opt/official-sources/data/official_sources.sqlite "SELECT COUNT(*) FROM source_candidates;"
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
du -sh /opt/official-sources/data/artifacts
ss -tulpn
```

Result:

- Initial VPS help check did not expose safe preview flags, so the candidate search was not run in
  normal write mode.
- Safe mode was implemented in `962f1e1` and the unmatched-row counting regression was fixed in
  `ab0c206`.
- Final deployed commit for the dry-run: `ab0c206`.
- Documents scanned: `3896`.
- Documents matched: `554`.
- Candidates created: `0`.
- Candidate count before/after: `0/0`.
- Artifact directory size before/after: `22M/22M`.
- DB validation after dry-run: `current_version=6 latest_version=6 status=valid`.
- Match counts by top keywords included `transporte=246`, `convocatoria=217`,
  `subvenciones=35`, `educación=28`, `ayuda=28`, `ayudas=27`, `vivienda=16`,
  `beca=10`, and `becas=10`.
- MCP privacy check found no MCP/FastMCP/Python/Uvicorn/official-sources public listener and no
  SQLite exposure.
- No BOE API calls, artifact downloads, downstream writes, approval, or publication were run.

TASK-004C-FIX3 local validation:

```bash
rtk python -m pytest tests/test_cli.py::test_find_boe_candidates_dry_run_does_not_create_candidates tests/test_cli.py::test_find_boe_candidates_no_write_alias_does_not_create_candidates tests/test_cli.py::test_find_boe_candidates_rejects_non_positive_limit tests/test_cli.py::test_find_boe_candidates_help_contains_false_positive_warning -q
rtk python -m pytest tests/test_cli.py::test_find_boe_candidates_ignores_documents_without_keyword_matches tests/test_cli.py::test_find_boe_candidates_dry_run_does_not_create_candidates tests/test_cli.py::test_find_boe_candidates_matches_titles_and_metadata -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- First red run failed as expected because `find-boe-candidates` did not accept `--dry-run` or
  `--no-write`, and help did not list safe preview options.
- Focused tests after implementation: `4 passed`.
- A VPS dry-run surfaced an additional matching bug before any writes occurred: documents without
  keyword matches were still counted because the warning envelope made every match object truthy.
  A regression test was added and failed before the fix.
- Focused matching regression tests after fix: `3 passed`.
- Full tests: `189 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- `--dry-run` and `--no-write` do not create `source_candidates`.
- `--limit` controls printed sample matches and rejects non-positive values.
- Documents without real keyword matches are not counted and do not produce sample rows.

TASK-004C-RUN1B VPS deployment and operational validation:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_15d5077_deploy_20260517_182109.sqlite
git fetch origin
git checkout main
git pull --ff-only origin main
python -m pip install -e .
official-sources --help
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db migrate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-boe-range --date-from 2026-04-18 --date-to 2026-05-17 --skip-existing --continue-on-no-publication --stop-on-error --max-days 30 --sleep-seconds 1
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date 2026-04-18
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date 2026-05-17
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date 2026-04-20
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
du -sh /opt/official-sources/data/artifacts
find /opt/official-sources/data/artifacts -type f | head -20
ss -tulpn
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_after_30d_backfill_20260517_182117.sqlite
```

Result:

- Initial deployment attempt stopped before pull because root Git access hit `dubious ownership`;
  the successful attempt used the `official-sources` service user for Git and package reinstall.
- Commit before deploy: `607b96c`.
- Deployed commit: `15d5077`.
- Pre-deploy backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- Migration: `current_version=6 latest_version=6 applied_migrations=none status=up_to_date`.
- DB validation after deploy: `current_version=6 latest_version=6 status=valid`.
- SQLite runtime status: `journal_mode=wal synchronous=normal`.
- Range result: `processed=0 skipped=30 success=0 no_publication=0 failed=0 days=30`.
- Final range state: `success=25 no_publication=5 failed=0`.
- HTTP status summary: `200:25,404:5`.
- Documents: `documents_fetched=3896 documents_new=3896 documents_updated=0`.
- Retry/throttle: `retry_count=0 throttle_events=6`.
- Artifact directory size: unchanged at `22M`.
- Post-run DB validation: `current_version=6 latest_version=6 status=valid`.
- Post-run backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- MCP privacy: no MCP/FastMCP/Python/Uvicorn/official-sources public listener and no SQLite exposure.
- No artifact downloads, candidate prefiltering, downstream integration, 24-month backfill, or full historical backfill were run.

TASK-004C-RUN1 patch local validation:

```bash
rtk python -m pytest tests/test_boe_adapter.py tests/test_cli.py::test_ingest_boe_summary_non_sunday_404_exits_nonzero_and_reports_failed tests/test_cli_db.py::test_cli_db_status_reports_versions_and_pending_migrations tests/test_storage_migrations.py::test_file_database_connection_enables_wal_and_normal_synchronous tests/test_storage_migrations.py::test_migrations_and_validation_work_with_wal_enabled_database -q
rtk python -m pytest tests/test_downstream_contract.py::test_pre_task_004b_downstream_checklist_exists tests/test_security_docs.py::test_boe_calendar_semantics_are_documented -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- First red run failed as expected before implementation: non-Sunday `404` still mapped to
  `no_publication`, WAL was not enabled, and `db status` did not report SQLite runtime pragmas.
- Documentation red run failed as expected before documentation updates: the pre-TASK-004B
  checklist did not exist and BOE calendar semantics were not explicit.
- Focused implementation tests: `26 passed`.
- Focused documentation tests after updates: `2 passed`.
- Full tests: `185 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- BOE daily `no_publication` is now Sunday-only unless a specific non-Sunday date is explicitly
  allowlisted from observed BOE API behavior.
- File-backed SQLite connections enable `journal_mode=wal` and `synchronous=normal`; in-memory
  test databases do not enable WAL by default.

TASK-004C-RUN1 VPS operational validation:

```bash
git pull --ff-only origin main
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_30d_backfill_20260517_180859.sqlite
official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-boe-range --date-from 2026-04-18 --date-to 2026-05-17 --skip-existing --continue-on-no-publication --stop-on-error --max-days 30 --sleep-seconds 1
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date 2026-04-18
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date 2026-05-17
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
du -sh /opt/official-sources/data/artifacts
ss -tulpn
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_after_30d_backfill_20260517_180948.sqlite
```

Result:

- Deployed commit: `607b96c`.
- Pre-run DB validation: `current_version=6 latest_version=6 status=valid`.
- Pre-run backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- Range result: `processed=29 skipped=1 success=25 no_publication=4 failed=0 days=30`.
- Final range state: `success=25 no_publication=5 failed=0`.
- HTTP status summary: `200:25,404:5`.
- Documents: `documents_fetched=3896 documents_new=3896 documents_updated=0`.
- Retry/throttle: `retry_count=0 throttle_events=6`.
- Artifact directory size: unchanged at `22M`.
- Post-run DB validation: `current_version=6 latest_version=6 status=valid`.
- Post-run backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- MCP privacy: no MCP/FastMCP/Python/Uvicorn/official-sources public listener and no SQLite exposure.
- No artifact downloads, candidate prefiltering, 24-month backfill, or full historical backfill were run.

TASK-004C local validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `175 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- Focused TASK-004C tests covered no-publication payload behavior, controlled range ingestion,
  range safety limits, local candidate prefiltering, structured cache misses, and separated
  summary/artifact status output.

TASK-004A-FIX2 local validation:

```bash
rtk python -m pytest tests/test_cli.py -q
rtk python -m ruff check src/official_sources/cli.py src/official_sources/storage/repository.py tests/test_cli.py
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Focused tests: `20 passed`.
- Focused lint: `All checks passed!`.
- Full tests: `155 passed`.
- Full lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- Status output now reports `summary_*` fields separately from `artifact_*` fields.
- Artifact HTTP summaries are read from `artifact_download_attempts`.
- Legacy `ingestion_status` and `last_http_status` remain summary aliases for compatibility.

TASK-004A-FIX1 local validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `152 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- New schema latest version: `6`.
- Focused no-publication behavior tests: BOE summary `404` persists `last_http_status=404`, records `status=no_publication`, exits zero from the CLI, skips artifact download, and keeps real 500/malformed-200 failures as `failed`.

TASK-004A-FIX1 VPS validation:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_no_publication_fix_20260517_173237.sqlite
git pull --ff-only origin main
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db migrate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
systemctl start official-sources-boe-daily.service
systemctl status official-sources-boe-daily.service --no-pager --full
journalctl -u official-sources-boe-daily.service -n 300 --no-pager
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date today
```

Result:

- Pre-update backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- Deployed commit: `a942899`.
- Migration: `current_version=6 latest_version=6 applied_migrations=6 status=migrated`.
- VPS DB validation: `current_version=6 latest_version=6 status=valid`.
- Forced BOE daily service: `service_start_exit=0`.
- systemd result: all three `ExecStart` commands ended with `status=0/SUCCESS`.
- Today status: `ingestion_status=no_publication last_http_status=404 documents=0 ... failed_downloads=0`.
- Artifact directory remained empty apart from the directory itself.
- MCP privacy remained intact: no MCP/FastMCP/Python/Uvicorn listener.

TASK-004A real VPS deployment rehearsal:

```bash
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'set -eu; whoami; hostname -f; date -Is; cat /etc/os-release | head -n 5; uname -a; command -v python3.12; command -v git; systemctl --version | head -n 1'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'mkdir -p /opt/official-sources/app /opt/official-sources/data/artifacts /opt/official-sources/data/backups /opt/official-sources/logs'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'useradd --system --home /opt/official-sources --shell /usr/sbin/nologin official-sources 2>/dev/null || true'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'chown -R official-sources:official-sources /opt/official-sources'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'sudo -u official-sources git clone https://github.com/Huntsman1756/official-sources-esp.git /opt/official-sources/app'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'cd /opt/official-sources/app; sudo -u official-sources python3.12 -m venv .venv; sudo -u official-sources .venv/bin/python -m pip install --upgrade pip; sudo -u official-sources .venv/bin/python -m pip install -e .; sudo -u official-sources .venv/bin/official-sources --help'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'CLI=/opt/official-sources/app/.venv/bin/official-sources; DB=/opt/official-sources/data/official_sources.sqlite; sudo -u official-sources $CLI --db-path $DB db status; sudo -u official-sources $CLI --db-path $DB db migrate; sudo -u official-sources $CLI --db-path $DB db validate'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'CLI=/opt/official-sources/app/.venv/bin/official-sources; DB=/opt/official-sources/data/official_sources.sqlite; BACKUP=/opt/official-sources/data/backups/official_sources_20260517_170440.sqlite; sudo -u official-sources $CLI --db-path $DB db backup --output $BACKUP; cp $BACKUP /tmp/official_sources_restore_test.sqlite; chown official-sources:official-sources /tmp/official_sources_restore_test.sqlite; sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db status; sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db migrate; sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db validate'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'cd /opt/official-sources/app; cp deploy/systemd/official-sources-boe-daily.service /etc/systemd/system/; cp deploy/systemd/official-sources-boe-daily.timer /etc/systemd/system/; cp deploy/systemd/official-sources-integrity-check.service /etc/systemd/system/; cp deploy/systemd/official-sources-integrity-check.timer /etc/systemd/system/; systemctl daemon-reload; systemctl enable official-sources-boe-daily.timer official-sources-integrity-check.timer; systemctl start official-sources-boe-daily.timer official-sources-integrity-check.timer'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'systemctl start official-sources-integrity-check.service; systemctl --no-pager --full status official-sources-integrity-check.service; journalctl -u official-sources-integrity-check.service -n 50 --no-pager'
```

Result:

- VPS access: successful as `root`.
- Environment: Ubuntu 24.04.4 LTS, Python 3.12, git, systemd 255.
- Application path: `/opt/official-sources/app`.
- Deployed commit: `c5b6350`.
- Package installation: `python -m pip install -e .` succeeded.
- CLI help printed successfully on the VPS.
- Database: migrated to `current_version=5 latest_version=5`.
- Database validation: `status=valid`.
- Backup: verified backup created at `/opt/official-sources/data/backups/official_sources_20260517_170440.sqlite`.
- Restore rehearsal: `/tmp/official_sources_restore_test.sqlite` status/migrate/validate passed.
- Smoke check: `status --date today` returned no documents and no failed downloads.
- systemd: both timers enabled and active.
- systemd smoke: `official-sources-integrity-check.service` ran with `status=0/SUCCESS`.
- MCP privacy: no MCP process, no `official-sources` listener, no public listener beyond SSH.
- Live BOE daily ingestion was not manually started; it is scheduled by timer.

TASK-004A dry-run after TASK-003F:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --help
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db backup --output G:/tmp/official-sources-task004a-20260517/backups/official_sources_20260517_000000.sqlite
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite --artifact-dir G:/tmp/official-sources-task004a-20260517/artifacts status --date today
```

Result:

- Preflight tests: `144 passed`.
- Lint: `All checks passed!`.
- Formatting: `55 files already formatted`.
- CLI help printed successfully from the source entry point.
- New temporary DB status: `current_version=0 latest_version=5 pending_migrations=5 status=pending`.
- Migration: `current_version=5 latest_version=5 applied_migrations=1,2,3,4,5 status=migrated`.
- Validation: `current_version=5 latest_version=5 status=valid`.
- Verified backup: `verification=quick_check source_check=ok backup_check=ok size_bytes=110592 status=success`.
- Restore copy status: `current_version=5 latest_version=5 pending_migrations=0 status=up_to_date`.
- Restore copy migration: `applied_migrations=none status=up_to_date`.
- Restore copy validation: `current_version=5 latest_version=5 status=valid`.
- No-network status smoke check for `2026-05-17`: `ingestion_status=none documents=0 ... failed_downloads=0`.

TASK-003F red validation:

```bash
rtk python -m pytest tests\test_boe_http_policy.py tests\test_boe_artifacts.py tests\test_cli.py tests\test_sqlite_backup.py tests\test_security_docs.py tests\test_downstream_contract.py -q
```

Result: failed during collection because `official_sources.sources.boe.http_policy` did not exist yet. This was the expected red step for the new BOE runtime policy.

TASK-003F focused validation:

```bash
rtk python -m pytest tests\test_boe_http_policy.py tests\test_boe_artifacts.py tests\test_cli.py tests\test_sqlite_backup.py tests\test_storage_migrations.py tests\test_security_docs.py tests\test_downstream_contract.py -q
```

Result: `64 passed`.

TASK-003F full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `144 passed`.
- Lint: `All checks passed!`.
- Formatting: `55 files already formatted`.

TASK-004A preflight validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `123 passed in 1.92s`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-004A local CLI and database dry-run:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --help
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db backup --output G:/tmp/official-sources-task004a/backups/official_sources_20260517_000000.sqlite
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite --artifact-dir G:/tmp/official-sources-task004a/artifacts status --date today
```

Result:

- CLI help printed successfully from the source entry point.
- New temporary DB status: `current_version=0 latest_version=4 pending_migrations=4 status=pending`.
- Migration: `applied_migrations=1,2,3,4 status=migrated`.
- Validation: `current_version=4 latest_version=4 status=valid`.
- Backup: `pages=26 status=success`.
- Restore copy status: `current_version=4 latest_version=4 pending_migrations=0 status=up_to_date`.
- Restore copy migration: `applied_migrations=none status=up_to_date`.
- Restore copy validation: `current_version=4 latest_version=4 status=valid`.
- No-network status smoke check for `2026-05-17`: `ingestion_status=none documents=0 ... failed_downloads=0`.

TASK-004A focused validation:

```bash
rtk python -m pytest tests\test_mcp_tools.py tests\test_systemd_templates.py -q
```

Result: `11 passed in 0.23s`.

TASK-004A final validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `125 passed`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-003E validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `123 passed`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-003D red test run:

```bash
rtk python -m pytest tests\test_sqlite_backup.py -q
```

Result: failed during collection because `official_sources.storage.backup` did not exist yet. This was the expected red step.

TASK-003D focused test run:

```bash
rtk python -m pytest tests\test_sqlite_backup.py -q
```

Result: `8 passed`.

TASK-003D full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `123 passed`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-003C red test run:

```bash
rtk python -m pytest tests\test_storage_migrations.py tests\test_cli_db.py -q
```

Result: failed during collection because `official_sources.storage.migrations` did not exist yet. This was the expected red step.

TASK-003C focused test run:

```bash
rtk python -m pytest tests\test_storage_migrations.py tests\test_cli_db.py -q
```

Result: `16 passed`.

TASK-003C full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `115 passed`.
- Lint: `All checks passed!`.
- Formatting: `48 files already formatted`.

TASK-003B red test run:

```bash
rtk python -m pytest tests\test_boe_consolidated.py tests\test_cli_consolidated.py tests\test_mcp_consolidated.py tests\test_citation.py -q
```

Result: failed during collection because the consolidated index/block parser and block ID validator did not exist yet. This was the expected red step.

TASK-003B focused test run:

```bash
rtk python -m pytest tests\test_boe_consolidated.py tests\test_cli_consolidated.py tests\test_mcp_consolidated.py tests\test_citation.py -q
```

Result: `42 passed`.

TASK-003B full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `99 passed`.
- Lint: `All checks passed!`.
- Formatting: `40 files already formatted`.

Initial red test run:

```bash
python -m pytest -q
```

Result: failed because the `official_sources` package did not exist yet. This was the expected red step.

TASK-001 implementation test run:

```bash
python -m pytest -q
```

Result: `30 passed`.

TASK-002 red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py -q
```

Result: failed because `official_sources.sources.boe.artifacts` did not exist yet. This was the expected red step.

TASK-002 focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py -q
```

Result: `11 passed`.

TASK-002B red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_cli.py -q
```

Result: failed because `official_sources.cli` did not exist yet. This was the expected red step.

TASK-002B focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_cli.py -q
```

Result: `9 passed`.

TASK-002C red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py tests/test_cli.py tests/test_systemd_templates.py -q
```

Result: failed because `artifact_download_attempts`, real failed download counts, `today` date support, and systemd templates did not exist yet. This was the expected red step.

TASK-002C focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py tests/test_cli.py tests/test_systemd_templates.py -q
```

Result: `29 passed`.

TASK-003 red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_consolidated.py tests/test_cli_consolidated.py tests/test_mcp_consolidated.py -q
```

Result: failed because consolidated legislation parser, storage, citation, CLI, and MCP tools did not exist yet. This was the expected red step.

TASK-003 focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_consolidated.py tests/test_cli_consolidated.py tests/test_mcp_consolidated.py -q
```

Result: `17 passed`.

Final test run, with bytecode writes disabled to avoid generated cache files:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Result: `76 passed`.

Lint:

```bash
RUFF_CACHE_DIR=G:/tmp/official-sources-ruff-cache python -m ruff check .
```

Result: `All checks passed!`

Format check:

```bash
RUFF_CACHE_DIR=G:/tmp/official-sources-ruff-cache python -m ruff format --check .
```

Result: `40 files already formatted`.

## Corrections During Validation

An intermediate `ruff` run found line-length and import-order issues. They were corrected with:

```bash
python -m ruff check . --fix
python -m ruff format .
```

After those corrections, the final validation commands passed.

TASK-002 intermediate validation also found line-length/format issues in the new artifact files. They were corrected with the same Ruff commands before final validation.

TASK-002B intermediate validation found import-order and formatting issues in the new CLI files. They were corrected with Ruff before final validation.

TASK-002C intermediate validation found import-order and formatting issues in the new audit and CLI changes. They were corrected with Ruff before final validation.

The final Ruff commands used an explicit cache directory under `G:/tmp` to avoid a local `.ruff_cache` permission warning. The commands exited successfully.

TASK-003 intermediate validation found one expected MCP tool-name regression test and formatting issues in the new consolidated legislation files. They were corrected before final validation.

TASK-003B intermediate validation found one MCP tool-name expectation that needed the new index and block tools, plus one formatting issue in `tests/test_boe_consolidated.py`. They were corrected before final validation.

TASK-003C intermediate validation found style and formatting issues in the new migration files and migration tests. They were corrected before final validation.

TASK-003D intermediate validation found style and formatting issues in the new backup module and smoke tests. They were corrected before final validation.

## Test Coverage Summary

Tests cover:

- BOE date validation.
- BOE fixture parsing.
- Official source creation.
- Document normalization.
- Citation generation.
- Citation/integrity separation.
- Deterministic artifact hashes.
- Raw-payload source snapshot hashes.
- Default signature status.
- Hash-change audit events.
- Mandatory ingestion runs, including failures.
- Candidate human-review defaults.
- MCP snake_case tool names.
- Structured MCP text envelopes.
- Instruction-like legal text containment.
- MCP integrity read access without mutation.
- No protected table writes from MCP tools.
- XML artifact download from mocked BOE URL.
- HTML artifact download from mocked BOE URL.
- PDF artifact download from mocked BOE URL.
- BOE artifact URL validation.
- Raw-byte artifact hashes and source snapshot hashes.
- Local cache paths for downloaded artifacts.
- Unchanged artifact integrity checks.
- Changed artifact integrity checks.
- MCP tools do not perform artifact downloads.
- XML/HTML extracted official text remains wrapped in structured MCP output.
- CLI help.
- CLI date validation.
- CLI BOE summary ingestion using fixture fetcher.
- CLI XML/HTML/PDF artifact download using mocked HTTP.
- CLI rejection of non-BOE artifact URLs.
- CLI local integrity checks for unchanged and changed cached artifacts.
- CLI status counts.
- CLI separation from MCP and external project mutation.
- Artifact download attempt audit rows for XML, HTML, and PDF.
- Failed artifact download audit rows with HTTP status when available.
- Rejected non-BOE URLs create a failed audit signal without unsafe fetching.
- Real failed download counts in CLI status.
- Separation between `artifact_download_attempts` and `integrity_checks`.
- `today` date support for timer-friendly CLI runs.
- systemd template existence and safety checks.
- Consolidated BOE identifier validation.
- Consolidated law XML metadata parsing from fixture.
- Consolidated law raw payload hash before parsing.
- Consolidated law storage, version storage, and text block storage.
- Consolidated law citation and block citation.
- Consolidated law payload hash-change integrity events.
- CLI consolidated-law retrieval with mocked HTTP.
- MCP consolidated-law metadata, text envelope, and citation tools.
- Prompt-injection-like consolidated text containment.
- No consolidated-law search stub.
- No legal interpretation or version diffing in MCP tools.
- Consolidated law safe block ID validation.
- Consolidated law text index fixture parsing.
- Nested consolidated law text index hierarchy preservation.
- Consolidated text index raw payload hashing before parsing.
- Consolidated text index source snapshot hash storage.
- Consolidated law official block endpoint fixture parsing.
- Consolidated block raw payload hashing before parsing.
- Consolidated block source snapshot hash storage.
- Consolidated block content storage.
- Consolidated block payload hash-change previous-hash preservation.
- Consolidated block payload hash-change integrity event creation.
- CLI consolidated text index retrieval with mocked HTTP.
- CLI consolidated text block retrieval with mocked HTTP.
- CLI consolidated block retrieval rejection for unsafe block IDs.
- CLI consolidated block content output only with explicit `--print-content`.
- MCP consolidated text index structured output.
- MCP consolidated block required structured envelope.
- MCP consolidated block citation output.
- Prompt-injection-like consolidated block text containment inside `content`.
- No downstream project writes from MCP tools.
- Empty SQLite database migration to the latest schema.
- Upgrade from a 0001-style initial schema to the latest schema.
- Upgrade from a database before `artifact_download_attempts`.
- Upgrade from a database before consolidated legislation tables.
- Upgrade from a database before consolidated block endpoint fields.
- Preservation of existing `official_documents`, `document_files`, `ingestion_runs`, and consolidated law block content during migrations.
- Fresh migrated schema equivalence with the canonical latest schema columns.
- Migration checksum recording.
- Idempotent re-run behavior without duplicate migration rows.
- Detection of applied migration checksum mismatch.
- Failed migration not marked as applied.
- `db status` version and pending migration reporting.
- `db migrate` application and up-to-date reporting.
- `db validate` valid and invalid database reporting.
- Rejection of directory paths as SQLite database paths for `db` commands.
- SQLite backup creation through the online backup API.
- Backup overwrite rejection unless `--force` is explicit.
- Backup readability with `PRAGMA integrity_check`.
- Restored backup opened from a temporary path.
- Restored realistic pre-latest database migrated to the latest schema.
- Restored database validation after migration.
- Representative data preservation after restore and migration.
- Read-only status, document citation, consolidated block citation, and MCP block envelope after restore and migration.
- CLI `db backup` help, success output, overwrite rejection, and explicit `--force`.
- Backup module does not use network clients, BOE APIs, MCP tools, or downstream write paths.

## Known Limitations

- Live BOE network calls were not used in tests.
- XML/HTML/PDF artifact download is controlled by stored BOE document URLs.
- Electronic signature validation is not implemented.
- PDF text extraction is not implemented.
- systemd files are templates only and are not installed by this repository.
- BOE consolidated legislation search is future work.
- BOE consolidated legal version comparison is not implemented.
- BOE consolidated text index and block tests use fixtures and mocked HTTP, not live BOE network access.
- BOE consolidated block retrieval stores official endpoint snapshots but does not determine legal applicability.
- SQLite migrations are lightweight Python migrations, not Alembic or ORM migrations.
- PostgreSQL migrations are not implemented.
- The migration CLI does not create backups; operators must create a backup before migrating persistent installations.
- Automatic restore over the active database is not implemented.
- Cloud backups, encryption, compression, and backup rotation are not implemented.
- TASK-003E added operational documentation and ADRs only; no new adapters, endpoints, deployment automation, RAG, downstream integrations, or legal interpretation were implemented.

## TASK-AUTO-009 - BOJA Evidence Review Decision Application

Operational validation was performed on the official-sources VPS for applying BOJA selected
candidate evidence review decisions.

VPS state before applying decisions:

```text
deployed_commit=6466f23
schema_version=8
journal_mode=wal
synchronous=normal
db_validate=valid
```

Selected candidates:

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

Pre-run checks:

```text
source_code=BOJA for all selected candidates
review_status=human_review_required for all selected candidates
pdf_available=10/10
pdf_hash_present=10/10
integrity_warnings=0
existing_candidate_evidence_reviews_for_selected=0
source_candidates=100
artifact_download_attempts=432
BOJA PDF document_files=10
artifact_directory_size=26M
```

Backup before mutation:

```text
path=/opt/official-sources/data/backups/official_sources_before_boja_evidence_review_apply_20260520_164233.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49049600
status=success
```

Applied evidence review decisions:

```text
accept_for_downstream_pilot: 77, 78, 80, 86
out_of_scope: 79, 81, 82, 87, 93, 98
needs_more_evidence: 0
false_positive: 0
defer: 0
```

Applied accepted fields:

```text
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
downstream_project_fit=EduAyudas
needs_pdf=no
selected_for_pdf=false
reviewed_by=Dani
reviewed_at=2026-05-20
```

Applied out-of-scope fields:

```text
manual_decision=out_of_scope
evidence_label=out_of_scope
evidence_review_status=out_of_scope
downstream_project_fit=neither
needs_pdf=no
selected_for_pdf=false
reviewed_by=Dani
reviewed_at=2026-05-20
```

Post-run verification:

```text
manual_decision.accept_for_downstream_pilot=4
manual_decision.out_of_scope=6
evidence_review_status.evidence_reviewed=4
evidence_review_status.out_of_scope=6
selected_for_pdf_count=0
needs_pdf_yes_count=0
pdf_available_count=10
source_candidates.review_status=human_review_required:100
artifact_download_attempts=432 -> 432
BOJA PDF document_files=10 -> 10
artifact_directory_size=26M -> 26M
db_validate=valid
```

MCP/privacy check:

```text
no matching listener observed for official, mcp, python, uvicorn, or fastmcp
```

Backup after validation:

```text
path=/opt/official-sources/data/backups/official_sources_after_boja_evidence_review_apply_20260520_164339.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49049600
status=success
```

No artifacts were downloaded, no candidates were created, no downstream project was touched, and no
approval or publication workflow was run.

## TASK-AUTO-010 - BOJA Pilot Closure

Documentation-only validation was performed locally for BOJA pilot closure.

Closure report:

```text
docs/reports/BOJA_PILOT_CLOSURE_2026-05-20.md
```

Pilot metrics summarized:

```text
30-day BOJA documents=1500
BOJA source_candidates_created=25
selected_for_evidence=10
PDFs_downloaded=10
accepted_for_downstream_pilot=4
out_of_scope_after_evidence_review=6
downstream_writes=0
approvals=0
publications=0
```

Safety state preserved by closure:

```text
database_mutation=0
new_artifacts=0
new_candidates=0
downstream_writes=0
approvals=0
publications=0
```

Validation:

```text
git diff --check: passed
```

No code changes were made, so the Python test suite was not run for this documentation-only closure.

## TASK-PLATFORM-001 - Downstream Onboarding Kit

Documentation-only validation was performed locally for the downstream onboarding kit.

Files created:

```text
docs/DOWNSTREAM_ONBOARDING.md
docs/examples/downstream_evidence_contract.example.json
docs/examples/downstream_profile.example.yaml
docs/reports/DOWNSTREAM_ONBOARDING_KIT_2026-05-20.md
```

Files updated:

```text
docs/DOWNSTREAM_CONTRACT.md
docs/ROADMAP.md
docs/SOURCES_POLICY.md
docs/VALIDATION.md
```

The kit documents:

```text
required downstream staging/review capabilities
evidence contract example
downstream profile template
manual export/import
preview-only import
evidence staging write
candidate creation as pending_review
draft creation after human decision
publication anti-patterns
project-specific onboarding notes
```

Validation:

```text
git diff --check: passed
```

No code changes were made, so the Python test suite was not run for this documentation-only task.

## TASK-MCP-COMPLIANCE-001 - MCP Official Compliance Hardening

MCP protocol hardening was performed locally before expanding source coverage further.

Files changed:

```text
src/official_sources/mcp/server.py
src/official_sources/storage/database.py
tests/test_mcp_protocol.py
tests/test_mcp_tools.py
tests/test_dogc_adapter.py
docs/MCP_TOOLS.md
docs/reports/MCP_OFFICIAL_COMPLIANCE_HARDENING_2026-05-23.md
docs/VALIDATION.md
```

Official MCP references used:

```text
https://modelcontextprotocol.io/specification/2025-11-25/basic
https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle
https://modelcontextprotocol.io/specification/draft/server/tools
https://modelcontextprotocol.io/specification/draft/basic/transports
https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
```

Validation:

```text
rtk python -m pip install -e .
rtk python -m pytest tests/test_mcp_protocol.py -q
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
Editable install completed; FastMCP 3.3.1 installed for protocol smoke tests.
tests/test_mcp_protocol.py: 4 passed
git diff --check: passed
pytest: 416 passed, 1 warning
ruff check: passed
ruff format --check: passed
```

Validated behaviors:

```text
MCP initialize negotiates protocolVersion=2025-11-25
serverInfo.name=official-sources
serverInfo.version=0.1.0
tools capability is advertised
tools/list returns deterministic described JSON Schema tools
tools/call returns structured content without creating candidates
stdio initialize writes JSON-RPC only to stdout
```

Follow-up documentation hardening added:

```text
docs/MCP_OFFICIAL_COMPLIANCE_GUIDE.md
docs/MCP_TOOLS.md
docs/VALIDATION.md
```

Validation:

```text
rtk git diff --check
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
ruff check: passed
ruff format --check: passed
```

## TASK-AUTO-BOPV-004B - BOPV Profile Calibration Review

BOPV candidate profile calibration was performed after the first real CLI dry-run showed
`matches_after_filters=1 / 489`.

Files changed:

```text
src/official_sources/cli.py
tests/test_cli.py
docs/reports/BOPV_CANDIDATE_PROFILE_CALIBRATION_2026-05-23.md
docs/VALIDATION.md
```

VPS state:

```text
deployed_commit=908e46f
source_candidates=146
artifact_download_attempts=482
BOPV official_documents=489
artifact_bytes=28857411
DB validation=status=valid schema_version=8
MCP privacy=no official/mcp/python/uvicorn/fastmcp listener output
```

Dry-run command:

```text
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-source-candidates --source BOPV --date-from 2026-04-21 --date-to 2026-05-20 --profile bopv-ayudas --dry-run --limit 200
```

Dry-run result:

```text
documents_scanned=489
matches_total=177
matches_after_filters=4
documents_matched=4
candidates_created=0
candidates_skipped_existing=0
excluded_by_keyword_rules=173
match_rate=0.82%
```

Safety result:

```text
source_candidates unchanged
artifact_download_attempts unchanged
artifact size unchanged
DB valid
no candidates created
no artifacts downloaded
no downstream writes
```

Local validation:

```text
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 418 passed, 1 warning
ruff check: passed
ruff format --check: passed
```

## TASK-AUTO-BOPV-005 - Limited BOPV Candidate Batch

Created a limited BOPV/EHAA candidate batch on the VPS.

Files changed:

```text
docs/reports/BOPV_30_DAY_CANDIDATE_BATCH_2026-05-23.md
docs/VALIDATION.md
```

VPS preparation:

```text
cd /opt/official-sources/app
git checkout main
git pull --ff-only origin main
python -m pip install -e .
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
```

Deployed commit:

```text
9557832
```

Pre-run state:

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

Candidate command:

```text
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite find-source-candidates --source BOPV --date-from 2026-04-21 --date-to 2026-05-20 --profile bopv-ayudas --limit 4 --write
```

Result:

```text
documents_scanned=489
matches_total=177
matches_after_filters=4
documents_matched=4
candidates_created=4
candidates_skipped_existing=0
review_status=human_review_required
```

Post-run state:

```text
source_candidates_total=150
BOPV source_candidates=4
BOPV review_status_distribution=human_review_required:4
artifact_download_attempts=482
artifact_bytes=28857411
DB validation=status=valid schema_version=8
MCP privacy=no matching official/mcp/python/uvicorn/fastmcp listeners
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_bopv_candidate_batch_20260524_043817.sqlite
```

Safety result:

```text
new BOPV candidates=4
new artifacts=0
artifact_download_attempts unchanged
downstream writes=0
approvals=0
publications=0
```

Docs-only validation:

```text
rtk git diff --check
```

Result:

```text
git diff --check: passed
```

## 2026-05-24 - BOPV 30-day candidate triage

Report:

```text
docs/reports/BOPV_30_DAY_CANDIDATE_TRIAGE_2026-05-23.md
```

Scope:

```text
metadata-only triage of BOPV candidates 147,148,149,150
```

VPS DB validation:

```text
/opt/official-sources/app/.venv/bin/official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

Post-review safety counters:

```text
source_candidates_total=150
BOPV source_candidates=4
BOPV review_status_distribution=human_review_required:4
artifact_download_attempts=482
artifact_bytes=28857411
MCP privacy=no matching official/mcp/python/uvicorn/fastmcp listeners
```

Triage result:

```text
reviewed=4
likely_relevant=1
unclear=2
out_of_scope=1
false_positive=0
selected_for_future_evidence=147,149,150
```

Docs-only validation:

```text
rtk git diff --check
```

Result:

```text
git diff --check: passed
```

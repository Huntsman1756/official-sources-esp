# BOJA Selected Candidate PDF Download - 2026-05-20

## Summary

TASK-AUTO-007C retried scoped BOJA PDF evidence download after TASK-AUTO-007B enriched `url_pdf`
for the selected BOJA candidates.

The final scoped download succeeded for all 10 selected candidates.

No candidates were created. No candidate review status changed. No downstream project was touched.
Nothing was approved or published.

## Selected Candidates

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

Verification before download:

```text
selected_count=10
source_code=BOJA for all selected candidates
review_status=human_review_required for all selected candidates
url_pdf present=10/10
pdf_url_domain=juntadeandalucia.es before URL canonicalization refresh
has_integrity_warning=false
```

## Code Adjustments During This Task

The first retry exposed a BOJA URL canonicalization issue:

```text
https://juntadeandalucia.es/eboja/...pdf -> HTTP 307
https://www.juntadeandalucia.es/eboja/...pdf -> HTTP 200 application/pdf
```

Two code fixes were made and validated:

```text
fb9d18f fix: normalize BOJA PDF evidence URLs
6466f23 fix: refresh BOJA enriched PDF URLs
```

The final behavior:

- BOJA PDF URLs from official detail metadata are normalized to the canonical `www.juntadeandalucia.es` host.
- Re-running BOJA URL enrichment refreshes existing persisted `url_pdf` values with the latest normalized official detail URL.
- Non-official and malformed PDF URLs remain rejected.

## Pre-Run State

Before retrying BOJA PDF download:

```text
source_candidates=100
artifact_download_attempts=402
BOJA PDF document_files=0
artifact_directory_size=24M
source_candidate review_status distribution=human_review_required:100
```

Pre-run backup:

```text
path=/opt/official-sources/data/backups/official_sources_before_boja_pdf_download_20260520_181523.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49033216
status=success
```

## Commands Executed

Initial scoped command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-boe-artifacts \
  --source BOJA \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98 \
  --types pdf
```

After discovering HTTP 307 redirects, code was fixed, deployed, and selected URLs were refreshed:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  enrich-boja-evidence-urls \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98
```

Final scoped download command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-boe-artifacts \
  --source BOJA \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98 \
  --types pdf
```

## Download Result

Final successful download result:

```text
selected_documents=10
artifact_types=pdf
downloaded=10
skipped=0
changed=0
failed=0
missing_artifact_url=0
retries=0
throttle_events=9
http_status_summary=pdf:200:10
```

Historical attempts for the selected candidates now include:

```text
skipped without URL: 10
failed HTTP 307 before canonicalization/refresh: 20
successful HTTP 200 PDF downloads: 10
```

The failed 307 attempts are retained as operational audit history. They do not represent current
evidence availability.

## Post-Run State

```text
source_candidates=100
BOJA selected candidates review_status=human_review_required:10
all source_candidates review_status=human_review_required:100
artifact_download_attempts=432
BOJA PDF document_files=10
selected_pdf_files=10
artifact_directory_size=26M
selected_integrity_warnings=0
```

Count changes from the start of TASK-AUTO-007C:

```text
artifact_download_attempts: 402 -> 432
BOJA PDF document_files: 0 -> 10
artifact_directory_size: 24M -> 26M
```

## DB Validation

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## MCP Privacy

Listener checks for `official`, `mcp`, `python`, `uvicorn`, and `fastmcp` returned no matching
listeners.

No public MCP listener or SQLite exposure was observed.

## Post-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_after_boja_pdf_download_20260520_161948.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49049600
status=success
```

## Validation

Code validation after BOJA URL normalization fixes:

```text
git diff --check: passed
rtk python -m pytest -q: 246 passed
rtk python -m ruff check .: passed
rtk python -m ruff format --check .: passed
```

VPS validation:

```text
db validate: valid
source candidate statuses: unchanged
artifact size: expected growth from PDF files
MCP privacy: no matching listener observed
```

## Known Limitations

- BOJA HTML evidence remains unavailable in the current path.
- BOJA XML evidence is not implemented.
- The command is still named `download-boe-artifacts`, although it now supports scoped BOJA PDFs.
- Artifact attempt history includes the earlier skipped and HTTP 307 attempts; reports should use
  current `document_files` and latest successful attempts when summarizing current evidence state.

## Recommendation

The selected BOJA candidates now have PDF evidence downloaded and can move to evidence review.

Recommended next task:

```text
TASK-AUTO-008 - BOJA selected candidate evidence review
```

Scope:

- review the 10 downloaded PDFs and metadata;
- classify as `accept_for_downstream_pilot`, `needs_more_evidence`, `out_of_scope`,
  `false_positive`, or `defer`;
- do not write downstream;
- do not approve or publish.

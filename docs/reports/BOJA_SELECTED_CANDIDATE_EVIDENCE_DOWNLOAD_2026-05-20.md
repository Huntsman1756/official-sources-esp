# BOJA Selected Candidate Evidence Download - 2026-05-20

## Summary

TASK-AUTO-007 added and exercised scoped BOJA evidence download support.

The command path now supports:

```bash
official-sources download-boe-artifacts \
  --source BOJA \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98 \
  --types pdf
```

The selected BOJA candidate records did not contain persisted `url_pdf`, `publicUrl`, or `pathPdf` values, so the scoped operation recorded explicit skipped attempts and did not download any files.

No candidates were approved. Nothing was published. No downstream projects were touched.

## Code Change

Commit:

```text
cbebb84 feat: add scoped BOJA evidence download
```

Implemented behavior:

- `download-boe-artifacts` now accepts `--source BOJA`;
- BOJA artifact downloads require explicit `--candidate-ids` or `--document-ids`;
- BOJA supports PDF only in this path;
- source mismatch is rejected;
- BOJA PDF URLs must use official `juntadeandalucia.es` eBOJA HTTPS paths;
- downloaded BOJA files would be cached under `artifacts/boja/...`;
- missing PDF URLs are recorded as skipped attempts, not invented.

The command name remains `download-boe-artifacts`; a future alias such as `download-source-artifacts` would be clearer.

## Selected Candidates

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

Verification result:

```text
selected_count=10
source_code=BOJA for all selected candidates
review_status=human_review_required for all selected candidates
```

## Evidence Fields Found

For all 10 selected candidates:

```text
url_html=null
url_xml=null
url_pdf=null
publicUrl=null
pathPdf=null
raw_metadata_json keys=date,id,number,organisation,summary,titleSec,boja_official_id
```

Available evidence before this task:

```text
json_metadata=already stored as BOJA raw API response during metadata ingestion
pdf=not available from persisted candidate/document metadata
html_public_page=not available from persisted candidate/document metadata
public_url_snapshot=not available from persisted candidate/document metadata
```

No evidence URL was invented.

## Pre-Run State

```text
source_candidates_total=100
BOJA source_candidates=25
selected_candidates=10
artifact_download_attempts=392
BOJA PDF document_files=0
artifact_directory_size=24M
DB validation=valid
```

## Pre-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_before_boja_selected_evidence_20260520_155142.sqlite
size=47M
status=created
```

## Command Executed

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

```text
selected_documents=10
artifact_types=pdf
downloaded=0
skipped=10
changed=0
failed=0
missing_artifact_url=10
retries=0
throttle_events=0
http_status_summary=none
```

Expected maximum attempts:

```text
10 candidates x 1 type = 10 attempts
```

Actual scoped attempts:

```text
pdf skipped=10
```

No HTTP download was attempted because no selected BOJA document had an official PDF URL.

## Post-Run State

```text
source_candidates_total=100
BOJA source_candidates=25
review_status_distribution=human_review_required:100
selected_review_status_distribution=human_review_required:10
artifact_download_attempts=402
BOJA PDF document_files=0
failed_downloads=0
artifact_directory_size=24M
DB validation=valid
```

Count changes:

```text
artifact_download_attempts: 392 -> 402
BOJA PDF document_files: 0 -> 0
artifact_directory_size: 24M -> 24M
```

## MCP Privacy

Listener checks for `official`, `mcp`, `python`, `uvicorn`, and `fastmcp` returned no matching listeners.

No public MCP listener or SQLite exposure was observed.

## Post-Run Backup

```text
path=/opt/official-sources/data/backups/official_sources_after_boja_selected_evidence_20260520_155218.sqlite
size=47M
status=created
```

## Validation

Local code validation:

```text
git diff --check: passed
rtk python -m pytest -q: 242 passed
rtk python -m ruff check .: passed
rtk python -m ruff format --check .: passed
```

VPS validation:

```text
db validate: valid
source candidate statuses: unchanged
artifact size: unchanged
MCP privacy: no matching listener observed
```

## Known Limitations

- The selected BOJA candidates do not currently contain persisted `publicUrl` or `pathPdf`.
- The BOJA metadata stored from the live 30-day backfill appears to include only compact search metadata for these documents.
- The scoped download path is implemented and tested, but it cannot download without an official URL.
- A future task must enrich BOJA document metadata by retrieving or reconstructing official evidence URLs from a verified official source. Do not infer URLs from titles or IDs without tests and source evidence.
- XML/HTML download for BOJA is not implemented. BOJA scoped artifact support is PDF-only for now.

## Recommendation

Do not proceed to evidence review yet because no PDFs were downloaded.

Recommended next task:

```text
TASK-AUTO-007B - BOJA evidence URL enrichment
```

Scope:

- determine the official BOJA detail or URL mechanism for selected documents;
- populate or update `url_pdf` / `url_html` only from verified official data;
- keep the operation scoped to selected candidates;
- no broad backfill, no downstream writes, no approvals, and no publication.

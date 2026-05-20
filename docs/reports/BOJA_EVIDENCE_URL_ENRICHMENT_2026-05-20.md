# BOJA Evidence URL Enrichment - 2026-05-20

## Summary

TASK-AUTO-007B diagnosed and fixed the BOJA evidence URL blocker discovered during
TASK-AUTO-007.

The scoped BOJA artifact downloader was already safe, but selected BOJA documents did not have
persisted `url_pdf`, `publicUrl`, or `pathPdf` values. The root cause was the BOJA search endpoint
field selection, not the downloader.

No PDFs were downloaded. No candidates were created, approved, or published. No downstream project
was touched.

## Selected Candidates Inspected

```text
77, 78, 79, 80, 81, 82, 86, 87, 93, 98
```

Pre-enrichment selected candidate state:

```text
selected_count=10
source_code=BOJA for all selected candidates
review_status=human_review_required for all selected candidates
url_pdf present=0/10
url_html present=0/10
raw_metadata_json URL-like fields=0/10
```

Stored raw metadata keys before enrichment:

```text
boja_official_id
date
id
number
organisation
summary
titleSec
```

## Diagnosis

Diagnosis category:

```text
search_endpoint_missing_fields
detail_endpoint_required
```

The stored BOJA metadata came from `GET /api/v0/boja/get/search_pagination` using its default
`campos` selection. The OpenAPI default includes:

```text
id
organisation
summary
number
date
titleSec
```

Those fields do not include PDF or public URL metadata.

This was not a downloader failure. It was also not a parser/persistence bug for the already stored
records, because the raw stored payload did not contain the URL fields.

## OpenAPI and Detail Endpoint Findings

Official OpenAPI:

```text
https://datos.juntadeandalucia.es/api/v0/boja/openapi.json
```

Relevant endpoint:

```text
GET /api/v0/boja/{bid}
```

The detail endpoint accepts the stable BOJA `id`, for example:

```text
disposition.2026.94.5
```

It returns structured JSON with:

```text
hits
total_hits
results[]
```

The relevant result fields include:

```text
id
date
number
summaryNoHtml
hasPdf
pdf[].pathPdf
pdf[].publicUrl
pdf[].hashPdf
pdf[].id_file
```

The detail response may also include full body fields. The enrichment code intentionally avoids
persisting `body` and `bodyNoHtml` in `raw_metadata_json`.

## Code Changes

Commit:

```text
1eb9070 fix: enrich BOJA evidence URLs
```

Implemented behavior:

- added BOJA detail URL building and detail fetch support;
- added `enrich-boja-evidence-urls`;
- parsed nested `pdf[]` metadata from BOJA detail responses;
- accepted only official HTTPS `juntadeandalucia.es` eBOJA PDF URLs;
- rejected non-official and malformed PDF URLs;
- preserved scoped operation by explicit `--candidate-ids` or `--document-ids`;
- updated only selected BOJA documents;
- avoided storing BOJA `body` / `bodyNoHtml` raw legal text in document metadata.

Command shape:

```bash
official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  enrich-boja-evidence-urls \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98
```

## Tests Added

Added fixture:

```text
tests/fixtures/boja_document_detail_with_pdf.json
```

Added tests for:

- parsing nested BOJA `pdf[].publicUrl`;
- preserving official BOJA PDF URL;
- rejecting non-official nested PDF URL;
- omitting `body` from enriched metadata;
- enriching only selected candidate documents;
- CLI enrichment by explicit candidate ID;
- no candidate creation during enrichment.

Validation:

```text
git diff --check: passed
rtk python -m pytest -q: 246 passed
rtk python -m ruff check .: passed
rtk python -m ruff format --check .: passed
```

## VPS Enrichment Run

Deployed commit:

```text
1eb9070
```

Pre-run backup:

```text
path=/opt/official-sources/data/backups/official_sources_before_boja_url_enrichment_20260520_160645.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=48996352
status=success
```

Command executed:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  enrich-boja-evidence-urls \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98
```

Result:

```text
selected_documents=10
enriched=10
skipped=0
failed=0
missing_evidence_url=0
retries=0
throttle_events=9
http_status_summary=200:10
```

Post-enrichment selected state:

```text
selected_with_url_pdf=10
url_html present=0/10
source_candidates_total=100
selected_review_status_distribution=human_review_required:10
all_review_status_distribution=human_review_required:100
artifact_download_attempts=402
BOJA PDF document_files=0
artifact_directory_size=24M
```

No PDF was downloaded.

Post-run backup:

```text
path=/opt/official-sources/data/backups/official_sources_after_boja_url_enrichment_20260520_160726.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=49033216
status=success
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

## Can TASK-AUTO-007 Be Retried?

Yes.

The selected BOJA documents now have official `url_pdf` values. The next task can retry the scoped
BOJA evidence download for the same 10 candidate IDs.

Recommended next task:

```text
TASK-AUTO-007C - Retry BOJA selected candidate evidence download
```

Expected command shape:

```bash
official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-boe-artifacts \
  --source BOJA \
  --candidate-ids 77,78,79,80,81,82,86,87,93,98 \
  --types pdf
```

## Known Limitations

- BOJA HTML evidence remains unavailable in the current path.
- BOJA XML evidence is not implemented.
- The enrichment command fetches detail JSON for explicit selected documents only; it is not a broad
  backfill tool.
- `url_html` remains null because the verified detail metadata exposed PDF URLs, not an HTML public
  page.
- The command name `download-boe-artifacts` remains semantically awkward for BOJA; a future alias
  `download-source-artifacts` would improve operator clarity.

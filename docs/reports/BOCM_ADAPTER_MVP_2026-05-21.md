# BOCM Adapter MVP

Date: 2026-05-21

## Summary

`TASK-AUTO-BOCM-002` implemented a metadata-only BOCM adapter MVP.

The adapter supports:

- date-to-issue discovery through the official BOCM date search endpoint;
- issue metadata ingestion through the official BOCM summary XML;
- normalized `official_documents` rows;
- official HTML, XML, JSON-LD, and PDF URL preservation;
- raw official payload hashing before parsing;
- `ingestion_runs` audit records;
- citation compatibility through the existing generic citation builder.

It does not create candidates, download PDFs, write downstream evidence, approve anything, or
publish anything.

## Endpoints Used

Official endpoints and URL patterns used by the MVP:

```text
https://www.bocm.es/search-day-month?field_date[date]=DD/MM/YYYY
https://www.bocm.es/boletin/bocm-YYYYMMDD-NNN
https://www.bocm.es/boletin/CM_Boletin_BOCM/YYYY/MM/DD/BOCM-YYYYMMDDNNN.xml
https://www.bocm.es/bocm-YYYYMMDD-DD
https://www.bocm.es/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-DD.xml
https://www.bocm.es/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-DD.json
```

The issue HTML URL is preserved as the public issue URL. The summary XML is used as the primary
document-list source because the live issue page is not a reliable static document index.

## Date-To-Issue Strategy

Preferred strategy:

```text
GET /search-day-month?field_date[date]=DD/MM/YYYY
```

The parser extracts an issue identifier matching:

```text
bocm-YYYYMMDD-NNN
```

For example:

```text
2026-05-20 -> bocm-20260520-118
```

## No-Publication Behavior

If the official date-search response contains the observed no-result text, the ingestion run is
recorded as:

```text
status=no_publication
documents_fetched=0
```

The adapter does not infer no-publication from weekday or calendar rules. Arbitrary HTTP or parser
errors are failures, not no-publication.

## Normalized Fields

For each BOCM document, the adapter stores:

- `external_id`: `BOCM:BOCM-YYYYMMDD-DD`
- `publication_date`
- `title`
- `department`
- `section`
- `document_type`
- `url_html`
- `url_xml`
- `url_pdf` as metadata only
- `raw_metadata_json.url_jsonld`
- `raw_metadata_json.issue_identifier`
- `raw_metadata_json.issue_url`

Document identifier policy:

```text
official_documents.external_id = BOCM:BOCM-YYYYMMDD-DD
raw_metadata_json.bocm_official_id = BOCM-YYYYMMDD-DD
```

Issue identifier policy:

```text
raw_metadata_json.issue_identifier = bocm-YYYYMMDD-NNN
```

## Raw Hash Policy

The MVP computes `source_snapshot_hash` from the exact raw official search response bytes plus the
exact raw official issue-summary XML bytes:

```text
search_day_response + BOCM_PAYLOAD_SEPARATOR + issue_summary_xml
```

The combined payload is stored as a `raw_api_response` document file for each parsed document. The
hash is computed before parsing normalized fields.

## CLI

New command:

```bash
official-sources ingest-bocm-date --date YYYY-MM-DD
```

CLI output includes:

- `status`
- `issue_identifier`
- `documents_fetched`
- `documents_new`
- `documents_updated`
- `retry_count`
- `throttle_triggered`
- `last_http_status`
- `source_snapshot_hash`

## Tests Added

Fixtures added:

- `tests/fixtures/bocm_search_day_with_issue.html`
- `tests/fixtures/bocm_search_day_no_publication.html`
- `tests/fixtures/bocm_issue_page.html`
- `tests/fixtures/bocm_issue_summary.xml`
- `tests/fixtures/bocm_document_jsonld.json`
- `tests/fixtures/bocm_document.xml`

Test coverage added:

- date validation;
- date-to-issue parsing;
- no-publication parsing;
- issue HTML document-list parsing;
- issue summary XML document-list parsing;
- official document URL preservation;
- XML URL preservation;
- JSON-LD URL preservation;
- raw hash computed before parsing;
- metadata ingestion success;
- metadata ingestion no-publication;
- no PDF document files by default;
- no candidate creation;
- no artifact download attempts;
- citation generation;
- CLI success and no-publication paths.

## Live Smoke

One controlled metadata-only live smoke was run for:

```text
2026-05-20
```

Result:

```text
status=success
issue_identifier=bocm-20260520-118
documents_fetched=100
documents_new=100
documents_updated=0
last_http_status=200
pdf_document_files=0
source_candidates=0
artifact_download_attempts=0
```

No PDFs were downloaded. No candidates were created. No downstream project was touched.

## Known Limitations

- The MVP is metadata-only.
- It does not download BOCM PDFs.
- It does not create BOCM candidates.
- It does not implement BOCM candidate profiles or evidence review.
- It does not parse full document text for downstream use.
- It relies on the issue summary XML as the authoritative document list after date-to-issue
  discovery.
- JSON-LD URLs are preserved but not fetched during date ingestion.
- PDF URLs may be stored as metadata when exposed by the summary XML, but PDF bytes are not
  downloaded.

## Next Recommended Task

Recommended next task:

```text
TASK-AUTO-BOCM-003 — Controlled BOCM 30-day metadata backfill
```

Scope should remain:

```text
metadata only
no PDFs
no candidates
no downstream
backup before/after
report
```

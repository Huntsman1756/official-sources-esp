# BOJA Adapter MVP - 2026-05-20

## Summary

TASK-AUTO-002 added a narrow BOJA metadata adapter MVP. The adapter uses the official Andalusian BOJA OpenAPI source and stores normalized document metadata in the existing generic storage model.

No candidates, downstream writes, artifact downloads, PDF text extraction, legal interpretation, RAG, approval, or publication workflow were implemented.

## Endpoint implemented

Official OpenAPI:

```text
https://datos.juntadeandalucia.es/api/v0/boja/openapi.json
```

Implemented endpoint:

```text
GET https://datos.juntadeandalucia.es/api/v0/boja/get/search_pagination
```

Implemented query shape:

```text
order_by=date
mode=DESC
size=200
page=0..n
date_from=YYYY-MM-DD
date_to=YYYY-MM-DD
```

Accepted content type:

```text
application/json
```

## CLI command

Added:

```bash
official-sources ingest-boja-date --date YYYY-MM-DD
```

The command:

- validates the date;
- fetches all available BOJA API pages for one date;
- creates an `ingestion_runs` row with `source_code=BOJA`;
- stores BOJA source metadata if missing;
- stores official document metadata;
- stores a `raw_api_response` file row with source snapshot hash;
- reports `pages_fetched` and `pagination_complete`;
- reports fetched/new/updated document counts;
- records empty result sets as `no_publication`.

## Data model

No migration or BOJA-specific table was added.

Reused tables:

```text
official_sources
official_documents
document_files
ingestion_runs
integrity_checks
```

BOJA source record:

```text
code=BOJA
name=Boletin Oficial de la Junta de Andalucia
jurisdiction=autonomous
region_code=ES-AN
access_type=official_api
reliability_level=canonical
```

External identifier policy:

```text
BOJA:<official_api_id>
```

Example:

```text
BOJA:disposition.2026.94.5
```

## Normalized fields

The MVP normalizes:

| Stored field | BOJA source field |
| --- | --- |
| `external_id` | `BOJA:` + API `id` |
| `publication_date` | API `date`, normalized from `DD/MM/YYYY` to `YYYY-MM-DD` |
| `title` | `title`, `summaryNoHtml`, or cleaned `summary` |
| `department` | `organisation` |
| `section` | `titleSec` |
| `document_type` | `type` or `subtitle` |
| `url_html` | `publicUrl` |
| `url_pdf` | `pathPdf`, converted to an absolute official URL if relative |
| `raw_metadata_json` | original item plus `boja_official_id` |

## Pagination, hash, and integrity behavior

TASK-AUTO-002B added pagination and completeness checks. The adapter uses BOJA `total_hits` metadata as the completeness target. It continues fetching pages until all expected documents are collected, or records a failed incomplete ingestion if pagination metadata is missing, ambiguous, or exceeds the configured safety limit.

For paginated responses, the adapter computes SHA-256 from a deterministic combined raw payload:

```text
page0_raw + "\n---BOJA-PAGE---\n" + page1_raw + ...
```

That combined hash is stored as the `source_snapshot_hash` for the `raw_api_response` document file. Hashing still happens before parsing and never from normalized fields.

This is an integrity signal only. It is not electronic signature validation.

## Citation example

BOJA citations use the generic citation builder and include:

```json
{
  "source_code": "BOJA",
  "source_name": "Boletin Oficial de la Junta de Andalucia",
  "external_id": "BOJA:disposition.2026.94.5",
  "title": "...",
  "publication_date": "2026-05-19",
  "official_url": "https://www.juntadeandalucia.es/...",
  "pdf_url": "https://www.juntadeandalucia.es/..."
}
```

## Empty/no-publication behavior

BOJA does not reuse BOE Sunday semantics.

Current MVP behavior:

```text
200 JSON with results=[] -> ingestion_runs.status=no_publication
```

HTTP errors, malformed JSON, invalid result structures, or database failures are recorded as failed ingestion runs.

## Fixtures and tests

Added fixtures:

```text
tests/fixtures/boja_date_with_documents.json
tests/fixtures/boja_date_empty_or_no_publication.json
tests/fixtures/boja_date_page_0.json
tests/fixtures/boja_date_page_1.json
tests/fixtures/boja_date_ambiguous_pagination.json
```

Added tests for:

- BOJA source record creation;
- date validation;
- parsing BOJA document fixture;
- empty/no-publication fixture;
- raw payload hash before parsing;
- source snapshot hash storage;
- official URL preservation;
- PDF path preservation as metadata;
- document normalization;
- ingestion runs for success and empty/no-publication;
- no PDF download by default;
- no candidate creation;
- citation generation;
- CLI command behavior.
- multi-page ingestion;
- pagination completeness reporting;
- max-page safety failure;
- ambiguous pagination metadata failure;

## Live smoke

A single-date live smoke was run against a temporary local database:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:\tmp\official-sources-boja-smoke-20260520\official_sources_boja_smoke.sqlite ingest-boja-date --date 2026-05-19
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:\tmp\official-sources-boja-smoke-20260520\official_sources_boja_smoke.sqlite db validate
```

Result:

```text
status=success
pages_fetched=1
pagination_complete=true
documents_fetched=72
documents_new=72
documents_updated=0
last_http_status=200
db_validate=status=valid
```

No PDF download, candidate extraction, downstream write, approval, or publication was run.

Do not run a broad BOJA range in this MVP task.

## Limitations

- No range command exists for BOJA yet.
- No PDF download is implemented for BOJA.
- No XML/HTML extraction is implemented for BOJA.
- No candidate extraction is implemented.
- No downstream evidence export/import is implemented.
- Rate-limit policy is conservative but BOJA-specific public quotas were not found.
- Completeness depends on BOJA continuing to expose reliable `total_hits`; missing pagination metadata now fails instead of silently storing partial results.
- The MVP does not validate electronic signatures.

## Next recommended task

```text
TASK-AUTO-003 - Controlled BOJA 30-day metadata backfill
```

Recommended scope:

- add a controlled BOJA date range command or wrapper;
- create pre/post DB backups for VPS use;
- run metadata-only backfill;
- no candidates;
- no downstream;
- no PDFs by default.

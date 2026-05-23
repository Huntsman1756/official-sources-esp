# DOGC Adapter MVP Local - 2026-05-23

## Scope

Implemented a local metadata-only DOGC adapter for one-date ingestion.

Explicitly not included:

- No VPS access.
- No backfills.
- No candidate creation.
- No artifact downloads.
- No downstream export changes.
- No MCP exposure.

## Official Endpoints Inspected

- `POST https://portaldogc.gencat.cat/eadop-rest/api/dogc/calendarDOGC`
  - Form parameters: `month`, `year`, `language`.
  - Used to map a date to `numDOGC` when `hasDOGC=true`.

- `POST https://portaldogc.gencat.cat/eadop-rest/api/dogc/searchDOGC`
  - JSON body with `publicationDateInitial` and `publicationDateFinal` in `DD/MM/YYYY`.
  - Used to list documents published on the target date.

- `POST https://portaldogc.gencat.cat/eadop-rest/api/dogc/documentDOGC`
  - Form parameters: `documentId`, `language`.
  - Used for document metadata and official PDF/RDF/Turtle/XML URLs as metadata only.

- `GET https://dogc.gencat.cat/ca/document-del-dogc/?documentId=...`
  - Public official HTML document URL preserved as metadata.

## CLI

Added:

```powershell
official-sources ingest-dogc-date --date YYYY-MM-DD
```

The command creates an `ingestion_run`, stores DOGC source metadata if needed, stores official documents, and records only raw API payload hashes / raw API response records. It does not download PDF, XML, RDF, Turtle, or HTML artifacts.

## Source Record

- `code`: `DOGC`
- `name`: `Diari Oficial de la Generalitat de Catalunya`
- `jurisdiction`: `autonomous`
- `region_code`: `ES-CT`
- `base_url`: `https://portaldogc.gencat.cat/eadop-rest/api/dogc`
- `access_type`: `official_api`
- `reliability_level`: `canonical`

## Fixtures and Tests

Added fixtures:

- `dogc_date_with_documents.json`
- `dogc_date_no_publication.json`
- `dogc_document_metadata.json`

Added tests for:

- Date validation.
- Official source creation.
- DOGC search payload date formatting.
- Date response parsing.
- No-publication response parsing.
- Document metadata normalization.
- URL preservation for HTML, XML, and PDF metadata.
- Citation generation.
- CLI success and no-publication paths.
- No PDF files downloaded.
- No source candidates created.
- No artifact download attempts created.

## Local Smoke

Executed smoke command with a temporary local SQLite database:

```powershell
official-sources --db-path <temp-db> ingest-dogc-date --date 2026-05-23
```

Result:

- `status=no_publication`
- `documents_fetched=0`
- `last_http_status=200`
- `source_snapshot_hash=f81f9ec879dbba32e7f10c9ee026e5bafeec19e0f22d5816f32b31f0246f9302`

This date was selected because the official calendar probe returned `hasDOGC=false`, keeping the smoke metadata-only and avoiding document artifact URLs beyond the no-publication run.

## Validation

Validation commands executed successfully:

```powershell
rtk git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Results:

- `rtk git diff --check`: passed.
- `rtk python -m pytest -q`: `366 passed`.
- `rtk python -m ruff check .`: passed.
- `rtk python -m ruff format --check .`: passed.

## Merge Risks

- Other source-adapter branches may touch `src/official_sources/cli.py` or `src/official_sources/storage/repository.py`, so command registration and source registration may need conflict resolution.
- DOGC `searchDOGC` does not include a stable CVE in the date search response; the adapter uses `documentDOGC` metadata to normalize the final external ID to `DOGC:<CVE>`.
- `calendarDOGC` is used by the live client to preserve the issue number. Fixtures also cover parser behavior without relying on a live network response.

# BOA Adapter MVP Local - 2026-05-23

## Scope

Implemented a local metadata-only adapter for BOA (Boletín Oficial de Aragón) under `official-sources ingest-boa-date --date YYYY-MM-DD`.

The adapter stores issue/document metadata, official BOA URLs as metadata, raw payload hash, citations, and ingestion runs. It does not create source candidates, does not download artifact files, and does not expose MCP functionality.

## Official Endpoint Strategy

The BOA Angular frontend calls the official CGI endpoint:

`https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI`

Date strategy:

`CMD=VERLST&BASE=BOLE&DOCS=1-250&SEC=OPENDATABOAJSONAPP&OUTPUTMODE=JSON&SORT=-PUBL&SEPARADOR=&PUBL=YYYYMMDD`

Observed behavior:

- Published dates return a JSON array encoded by the official BOA service.
- No-publication dates return the official BOA HTML page with `No se han recuperado documentos`.
- Document PDF URLs are exposed in the JSON `UrlPdf` field and are preserved as metadata only.
- Full-issue PDF URLs are exposed in `UrlBCOM` and are preserved under raw metadata as `issue_pdf_url`.
- No XML URL was available in the observed date endpoint payload.

## Source Registration

Added source:

- `code`: `BOA`
- `name`: `Boletín Oficial de Aragón`
- `jurisdiction`: `autonomous`
- `region_code`: `ES-AR`
- `base_url`: `https://www.boa.aragon.es`
- `access_type`: `official_json`
- `reliability_level`: `canonical`

## Tests And Fixtures

Added fixtures:

- `boa_date_with_documents.json`
- `boa_date_no_publication.html`
- `boa_document_metadata.json`

Added coverage:

- date validation
- source registration
- published-date parsing
- no-publication parsing
- document metadata normalization
- official URL preservation
- raw payload hash preservation
- metadata-only ingestion with no artifact/candidate writes
- citation generation
- CLI success and no-publication paths

## Smoke

Local smoke uses a temporary SQLite database and fixture-backed fetcher. It does not contact VPS, run backfills, create candidates, download artifacts, or touch downstream exports.

Result:

`exit_code=0 status=success documents_fetched=2 candidates=0 artifact_attempts=0 files=raw_api_response:2`

## Validation

- `rtk git diff --check`: passed
- `rtk python -m pytest -q`: `365 passed`
- `rtk python -m ruff check .`: passed
- `rtk python -m ruff format --check .`: passed

## Merge Risks

- BOA `UrlPdf` currently contains two official URLs separated by BOA frontend delimiters; the adapter preserves the first URL as document PDF metadata and the first `UrlBCOM` URL as issue PDF metadata.
- BOA no-publication behavior is HTML, not JSON, so future official page copy changes could require parser adjustment.
- The MVP intentionally does not paginate beyond `DOCS=1-250`; observed daily issue counts fit this envelope, but very large future issues may require pagination.

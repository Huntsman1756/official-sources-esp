# DOGV Adapter MVP

Date: 2026-05-21

## Objective

Implement a minimal metadata-only DOGV adapter for `official-sources`.

This task did not implement candidate extraction, PDF download, XML/HTML artifact download, downstream integration, MCP tools, RAG, or legal interpretation.

## Files Changed

- `src/official_sources/sources/dogv/__init__.py`
- `src/official_sources/sources/dogv/client.py`
- `src/official_sources/sources/dogv/parser.py`
- `src/official_sources/sources/dogv/ingestion.py`
- `src/official_sources/cli.py`
- `src/official_sources/storage/repository.py`
- `tests/test_dogv_adapter.py`
- `tests/test_cli_dogv.py`
- `tests/fixtures/dogv_date_with_documents.json`
- `tests/fixtures/dogv_date_no_publication.json`
- `tests/fixtures/dogv_document_metadata.json`
- `docs/AUTONOMOUS_BULLETINS_RESEARCH.md`
- `docs/SOURCES_POLICY.md`
- `docs/ROADMAP.md`
- `docs/VALIDATION.md`
- `docs/reports/DOGV_ADAPTER_MVP_2026-05-21.md`

## Implemented Endpoints

The MVP implements one-date DOGV metadata ingestion from the official DOGV backend:

```text
GET https://dogv.gva.es/dogv-portal/dogv?date=YYYY-MM-DD&lang=es
```

The adapter also preserves official URL references for later scoped evidence work:

```text
https://dogv.gva.es/es/resultat-dogv?signatura=YYYY/NNNNN
https://dogv.gva.es/dogv-portal/disposicion/metadata/{id}?lang=es
https://dogv.gva.es/dogv-portal/export/disposicion/xml/dinamico/{id}?lang=es
https://dogv.gva.es/datos/YYYY/MM/DD/pdf/YYYY_NNNNN_es.pdf
```

These URLs are stored as metadata only. No XML, HTML, or PDF artifacts are downloaded by this MVP.

## CLI

Added:

```bash
official-sources ingest-dogv-date --date YYYY-MM-DD
```

CLI output includes:

```text
status
issue_identifier
documents_fetched
documents_new
documents_updated
retry_count
throttle_triggered
last_http_status
source_snapshot_hash
```

## Data Model

The adapter reuses existing generic tables:

```text
official_sources
official_documents
document_files
ingestion_runs
integrity_checks
artifact_download_attempts
```

New source record:

```text
code = DOGV
name = Diari Oficial de la Generalitat Valenciana
jurisdiction = autonomous
region_code = ES-VC
base_url = https://dogv.gva.es/dogv-portal
access_type = official_json
reliability_level = canonical
```

No DOGV-specific tables were added.

## Identifier Policy

Issue identifier:

```text
cabecera.numeroDogv
```

Example:

```text
10366
```

Document identifier:

```text
DOGV-C-YYYY-NNNNN
```

This is derived from DOGV metadata when available. For date-list records, it is derived from `codigoInsercion`, for example:

```text
codigoInsercion = 2026/16061
official_identifier = DOGV-C-2026-16061
external_id = DOGV:DOGV-C-2026-16061
```

## No-Publication Behavior

Observed DOGV no-publication shape:

```json
{
  "cabecera": null,
  "disposiciones": null,
  "fechaSumario": null,
  "urlPdf": null
}
```

Implemented behavior:

- `200` with issue header and documents -> `success`.
- `200` with null or missing issue/documents -> `no_publication`.
- 4xx, 5xx, network errors, malformed JSON, or parser errors -> `failed`.

No-publication is not inferred only from weekday.

## Normalized Fields

The date JSON parser normalizes:

```text
official_identifier
external_id
publication_date
title
department
section/subsection
official HTML URL
dynamic XML URL
official PDF URL
metadata URL
issue identifier
raw DOGV document metadata
```

The optional document metadata parser also supports DOGV document metadata JSON and preserves:

```text
identifier
documentNumber
journal_number
section
subsection
range
author
metadata_sha256
source_metadata
```

## Raw Hash Policy

`source_snapshot_hash` is computed from the raw DOGV date JSON bytes before parsing.

For the current MVP, each document receives a `raw_api_response` `document_files` row pointing to the official date endpoint and storing the raw date JSON hash. This does not download external artifacts.

## Citation Example

Example citation inputs for `DOGV:DOGV-C-2026-16061`:

```text
source_code = DOGV
source_name = Diari Oficial de la Generalitat Valenciana
official_identifier = DOGV-C-2026-16061
title = EXTRACTO de la Resolucion de 13 de mayo de 2026...
official_url = https://dogv.gva.es/es/resultat-dogv?signatura=2026/16061
publication_date = 2026-05-20
```

## Tests Added

Added tests for:

- DOGV source record creation.
- Date validation.
- Parsing date JSON with documents.
- Parsing no-publication JSON.
- Document metadata normalization.
- Issue identifier preservation.
- Official HTML/XML/PDF URL preservation.
- Raw hash computed before parsing.
- Ingestion run success.
- Ingestion run no-publication.
- No PDF download by default.
- No candidate creation.
- Citation generation.
- CLI command behavior.

No test depends on live DOGV network access.

## Live Smoke

Controlled local smoke with a temporary SQLite database:

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

The smoke was metadata-only. No candidates, downstream writes, or PDF download commands were run.

## Validation

```text
tests/test_dogv_adapter.py tests/test_cli_dogv.py: 15 passed
BOJA/BOCM/DOGV adapter+CLI focused tests: 64 passed
```

Full validation was run after documentation updates:

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

## Known Limitations

- No formal DOGV OpenAPI document was found.
- The adapter relies on official backend endpoints used by the DOGV frontend.
- No XML/HTML artifact download is implemented.
- No PDF download is implemented.
- No candidate extraction is implemented.
- No downstream export or import is implemented.
- Special issue handling uses preserved metadata only; broader backfill should verify `esBis` behavior.
- Dynamic XML URLs are preserved but not fetched during metadata ingestion.

## Next Recommended Task

```text
TASK-AUTO-DOGV-003 - Controlled DOGV 30-day metadata backfill
```

Scope should remain:

```text
metadata only
no PDFs
no candidates
no downstream
backup before/after
DB validation
MCP privacy check
report
```

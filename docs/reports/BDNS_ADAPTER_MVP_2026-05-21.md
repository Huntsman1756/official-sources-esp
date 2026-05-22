# BDNS Metadata Adapter MVP

Date: 2026-05-21

## Summary

TASK-BDNS-002 implemented a metadata-only BDNS adapter MVP for public grant/subsidy calls
(`convocatorias`).

BDNS is modeled as a primary grants registry, not as an official bulletin.

Scope completed:

```text
convocatorias only
metadata only
latest calls
detail by numConv/codigoBDNS
limited search command
raw JSON hash before parsing
citation support through existing document citation builder
no concessions
no candidates
no downstream writes
no artifact downloads
```

## Endpoints Implemented

Base URL:

```text
https://www.infosubvenciones.es/bdnstrans/api
```

Implemented endpoints:

```text
GET /convocatorias/ultimas?page=N&pageSize=N
GET /convocatorias?numConv=<codigoBDNS>
GET /convocatorias/busqueda?page=N&pageSize=N&fechaDesde=DD/MM/YYYY&fechaHasta=DD/MM/YYYY
```

Deferred endpoint:

```text
GET /concesiones/busqueda
```

Concesiones are intentionally excluded from the MVP because they require a separate
privacy/retention review.

## Data Model Decision

The MVP reuses existing generic storage:

```text
official_sources
official_documents
document_files
ingestion_runs
```

No BDNS-specific tables were added.

Source record:

```text
code=BDNS
name=Base de Datos Nacional de Subvenciones
jurisdiction=state
region_code=ES
access_type=official_api
reliability_level=canonical
```

The current `official_sources` table has no `source_family` column. The adapter therefore stores
source-family semantics in document metadata:

```text
source_family=grants_registry
resource_type=grant_call
```

This keeps the MVP compatible with the existing schema while avoiding bulletin-specific issue
semantics.

## Identifier Strategy

Primary external identifier:

```text
BDNS:<codigoBDNS>
```

Examples:

```text
BDNS:907042
BDNS:907364
```

Stored fields:

```text
external_id=BDNS:<codigoBDNS>
official_identifier=BDNS:<codigoBDNS>
bdns_code=<codigoBDNS or numeroConvocatoria>
bdns_internal_id=<id>
```

The adapter does not construct identifiers from title/date text.

## Fields Normalized

The MVP normalizes at least:

```text
codigo_bdns / bdns_code
title
calling_body / department
publication_date
registration_date
application_start_date
application_end_date
budget
beneficiary_type
instrument_type
sector_activity
territorial_scope
official_url / BDNS public URL
application_url
base_regulation_url
raw_data
```

Field variability handled:

```text
numeroConvocatoria / codigoBDNS / codigoBdns / codigo
fechaPublicacion / fechaRecepcion / fechaRegistro
presupuestoTotal / presupuesto / importeTotal / importe
content / items
```

## CLI Commands

Added:

```bash
official-sources ingest-bdns-latest --limit N
official-sources ingest-bdns-call --num-conv CODIGO_BDNS
official-sources search-bdns-calls --date-from DD/MM/YYYY --date-to DD/MM/YYYY --page-size N --max-pages N
```

Pagination and size limits:

```text
default page_size=10
hard max page_size=100
default max_pages=1
hard max_pages=10
```

The search command is intentionally bounded and is not a broad historical downloader.

## Raw Hash Policy

The adapter computes `source_snapshot_hash` from exact raw JSON response bytes before parsing.

For latest/search pages, the raw page response is stored as `raw_api_response` for each normalized
call in that page. For detail ingestion, the raw detail JSON is stored as `raw_api_response` for the
single call.

No PDF, HTML, XML, or external document artifact is downloaded.

## Citation Example

Existing citation builder output for a BDNS call includes:

```json
{
  "source_code": "BDNS",
  "source_name": "Base de Datos Nacional de Subvenciones",
  "external_id": "BDNS:907042",
  "official_url": "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/907042",
  "publication_date": "2026-05-20"
}
```

## Tests Added

Fixtures:

```text
tests/fixtures/bdns_latest_convocatorias.json
tests/fixtures/bdns_search_convocatorias.json
tests/fixtures/bdns_convocatoria_detail.json
tests/fixtures/bdns_empty_results.json
tests/fixtures/bdns_not_found.json
```

Test files:

```text
tests/test_bdns_adapter.py
tests/test_cli_bdns.py
```

Covered behavior:

```text
BDNS source record creation
Spanish date filter validation
latest calls parsing
search result parsing
detail by numConv parsing
empty/no-results parsing
not-found/missing detail failure path
raw hash before parsing
latest ingestion
detail ingestion
citation generation
pagination limits
no concessions in MVP
no candidates
no artifact download attempts
CLI latest command
CLI detail command
CLI search limit validation
```

## Live Smoke

Controlled local live smoke used a temporary SQLite database.

Latest call smoke:

```text
command=ingest-bdns-latest --limit 1
status=success
documents_fetched=1
documents_new=1
documents_updated=0
last_http_status=200
retry_count=0
source_snapshot_hash=50601c432d0c07af46e508b89d53250d9f4eee0aabffb6d265be10ab1fc1ce6d
```

The latest call produced:

```text
num_conv=907364
```

Detail smoke:

```text
command=ingest-bdns-call --num-conv 907364
status=success
official_identifier=BDNS:907364
documents_fetched=1
documents_new=0
documents_updated=1
last_http_status=200
retry_count=0
source_snapshot_hash=b36afff906d5c4fc1b79394acb51b12844c4988813b7408aeb7057bf76a0749b
```

Temporary DB validation:

```text
status=valid
```

The smoke did not touch the project VPS DB and did not create candidates, downstream writes, or
artifact downloads.

## Validation

```text
git diff --check: passed
rtk python -m pytest -q: 299 passed
rtk python -m ruff check .: passed
rtk python -m ruff format --check .: passed
```

## Known Limitations

BDNS concessions are not implemented.

The adapter does not download external documents, PDFs, HTML, XML, base-regulation documents, or
application pages.

The adapter does not create source candidates or downstream exports.

The existing `official_sources` table does not have a first-class `source_family` column, so
`grants_registry` is preserved in per-document metadata for now.

The search command is intentionally bounded and should not be used for broad backfills without a
separate task, backup plan, and report.

## Next Recommended Task

Recommended next task:

```text
TASK-BDNS-003 — Controlled BDNS latest calls ingestion
```

Scope should remain:

```text
latest calls only
small explicit limit
metadata only
no concessions
no candidates
no downstream
backup/report if run on VPS
```

# BORM Adapter MVP Local - 2026-05-23

## Scope

Task: `TASK-AUTO-BORM-002`.

Implemented a local metadata-only adapter for BORM:

- Source code: `BORM`
- Name: `Boletin Oficial de la Region de Murcia`
- Jurisdiction: `autonomous`
- Region code: `ES-MC`
- Access type: `official_xml`
- Reliability level: `canonical`

Explicitly not performed:

- No VPS connection.
- No backfills.
- No source candidates.
- No artifact downloads.
- No downstream export or MCP exposure.

## Official Endpoint Discovery

Primary metadata endpoint:

- `https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml`

Supporting official/catalog pages:

- `https://www.borm.es/`
- `https://datosabiertos.regiondemurcia.es/carm/catalogo/sector-publico/indices-del-boletin-oficial-de-la-region-de-murcia-ano-actual`
- `https://datos.gob.es/es/catalogo/a14002961-indices-del-boletin-oficial-de-la-region-de-murcia-ano-actual`

Safe probes performed locally:

- `HEAD https://www.borm.es/` returned `200`.
- `HEAD https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml` returned `200`.
- `GET https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml` returned XML metadata, not document artifacts.
- JSON/CSV variants returned a Radware captcha page from the local probe environment; XML was usable.

The open-data/catalog metadata documents the index fields including publication type,
announcement ID, digital object ID, publication number/date, summary, administration, section,
announcer, NPE, HTML URL, PDF URL, and pages.

## Date Strategy

The adapter fetches the official current-year XML index and filters records where
`Fec_Publicacion` starts with the target `YYYY-MM-DD`.

Observed probe:

- `2026-05-20`: 41 records in issue `114/2026`.
- `2026-05-17`: 0 records, treated as controlled `no_publication`.

## Metadata Mapping

For each matching XML `resultado`:

- `external_id`: `BORM:{NPE}`
- `official_identifier`: `NPE`
- `publication_date`: date part of `Fec_Publicacion`
- `title`: `Sumario`
- `department`: `Anunciante`, falling back to `Administracion`
- `section`: `Seccion`
- `document_type`: `Rango`
- `url_html`: `URL_HTML`
- `url_pdf`: `URL_PDF`
- `url_xml`: not available per document in the discovered index
- `raw_metadata`: BORM fields plus issue-level PDF and summary PDF metadata URLs
- `source_snapshot_hash`: SHA-256 of the raw XML payload

The CLI stores the raw XML endpoint snapshot as `raw_api_response` metadata for integrity tracking.
It does not download PDFs, HTML, XML document artifacts, or create candidates.

## CLI

Added:

```powershell
official-sources ingest-borm-date --date YYYY-MM-DD
```

Implementation path:

- `src/official_sources/sources/borm/client.py`
- `src/official_sources/sources/borm/parser.py`
- `src/official_sources/sources/borm/ingestion.py`
- `src/official_sources/cli.py`
- `src/official_sources/storage/repository.py`

## Fixtures And Tests

Fixtures:

- `tests/fixtures/borm_date_with_documents.xml`
- `tests/fixtures/borm_date_no_publication.xml`
- `tests/fixtures/borm_document_metadata.xml`

Tests:

- Date validation.
- Source record creation.
- Date response with documents.
- No-publication response.
- Document metadata normalization.
- URL preservation.
- Citation generation.
- CLI ingestion.
- No candidate creation.
- No PDF/artifact download attempts.

Focused result:

```text
rtk python -m pytest -q tests\test_borm_adapter.py tests\test_cli_borm.py
16 passed
```

## Local Smoke

Local temporary SQLite smoke against the official XML endpoint:

```text
rtk python -c "... run(['--db-path', temp_db, 'ingest-borm-date', '--date', '2026-05-20']) ..."
command_started=ingest-borm-date source_code=BORM target_date=2026-05-20
status=success issue_identifier=114/2026 documents_fetched=41 documents_new=41 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200 source_snapshot_hash=3fbefcbb1b9b842f94daebac0a7c48b4c9e9cebd56b3fed9b91580212c8853df
exit_code 0
```

Smoke database checks:

```text
documents 41
candidates 0
artifact_attempts 0
pdf_files 0
raw_snapshots 41
```

## Final Validation

```text
rtk git diff --check
passed

rtk python -m pytest -q
367 passed

rtk python -m ruff check .
All checks passed!

rtk python -m ruff format --check .
101 files already formatted
```

## Merge Risks

- The BORM open-data XML endpoint is current-year oriented. Historical years may need archived
  annual resources in a later adapter hardening task.
- The XML endpoint is accessible from local probes, while JSON/CSV variants were blocked by captcha.
- The adapter stores one raw index snapshot per ingested document, following the existing repository
  schema pattern for raw metadata snapshots.

# BOCYL Metadata Adapter MVP - 2026-05-21

## Scope

Implemented a metadata-only BOCYL adapter MVP for `official-sources`.

This task did not:

- create candidates;
- download PDF/XML/HTML artifacts;
- write downstream;
- touch EduAyudas;
- touch `la-ayuda`;
- expose MCP;
- run a broad backfill;
- implement other adapters;
- touch VPS.

## Implemented Endpoints

Primary metadata endpoint:

```text
GET https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl/records?limit=100&where=fecha_publicacion=date'YYYY-MM-DD'
```

Implemented CLI:

```bash
official-sources ingest-bocyl-date --date YYYY-MM-DD
```

The adapter preserves official artifact URLs returned by the API:

```text
enlace_fichero_html
enlace_fichero_xml
enlace_fichero_pdf
```

It stores these as document metadata only. It does not fetch those artifacts.

## Date and No-Publication Behavior

Date ingestion validates `YYYY-MM-DD` input and queries the official API by
`fecha_publicacion`.

Behavior:

| Condition | Run status |
| --- | --- |
| API returns records | `success` |
| API returns zero records | `no_publication` |
| HTTP/network/parser/storage error | `failed` |

No-publication is based on the official API result count, not on weekday
inference.

## Normalized Fields

Source:

```text
code=BOCYL
name=Boletín Oficial de Castilla y León
jurisdiction=autonomous
region_code=ES-CL
access_type=official_json
reliability_level=canonical
```

Document fields:

| Stored field | BOCYL source field / rule |
| --- | --- |
| `external_id` | `BOCYL:<document_identifier>` |
| `publication_date` | `fecha_publicacion` |
| `title` | `titulo` |
| `department` | `organismo` |
| `section` | `seccion` |
| `document_type` | `rango` |
| `url_html` | `enlace_fichero_html` |
| `url_xml` | `enlace_fichero_xml` |
| `url_pdf` | `enlace_fichero_pdf` |
| `raw_metadata_json` | issue id, document id, page range, subsection, apartado, suborganism, raw API record |

The raw date API JSON is hashed before parsing and stored as
`source_snapshot_hash`.

## Identifier Strategy

Issue identifier:

```text
issue_identifier = no_edicion
example: 94/2026
```

Document identifier:

```text
document_identifier = BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ
external_id = BOCYL:<document_identifier>
example: BOCYL:BOCYL-D-20052026-94-1
```

The document identifier is extracted from official PDF/XML/HTML artifact URLs.
It is not derived from title text.

## Citation Example

Example document:

```text
external_id=BOCYL:BOCYL-D-20052026-94-1
publication_date=2026-05-20
issue_identifier=94/2026
official_url=http://bocyl.jcyl.es/html/2026/05/20/html/BOCYL-D-20052026-94-1.do
```

The citation layer resolves the official URL from `url_html` first, then XML/PDF
if needed.

## Tests Added

Added fixtures:

```text
tests/fixtures/bocyl_date_with_documents.json
tests/fixtures/bocyl_date_no_publication.json
tests/fixtures/bocyl_document_metadata.json
```

Added tests:

```text
tests/test_bocyl_adapter.py
tests/test_cli_bocyl.py
```

Covered behavior:

- source record creation;
- date validation;
- published date parsing;
- no-publication parsing;
- document metadata normalization;
- issue/document identifier strategy;
- HTML/XML/PDF URL preservation;
- raw hash computed before parsing;
- ingestion run success;
- ingestion run no-publication;
- no PDF downloads by default;
- no artifact download attempts;
- no candidates created;
- citation generation;
- CLI command.

## Controlled Live Smoke

Run locally against a temporary SQLite database using `official_sources.cli.run`
with `PYTHONPATH=src`.

Published date:

```text
date=2026-05-20
status=success
issue_identifier=94/2026
documents_fetched=42
documents_new=42
documents_updated=0
last_http_status=200
source_snapshot_hash=3f35ffbebaf92bd1bf0a6c9c46c404ba79672f4d351d2fed7c442b15de6f54ef
```

No-publication date:

```text
date=2026-05-17
status=no_publication
documents_fetched=0
documents_new=0
documents_updated=0
last_http_status=200
source_snapshot_hash=b40a5ce424590aa2d85084c9a423d90252d3ba8a22202193a62874533698a3a3
```

Safety checks on the temporary database:

```text
official_documents=42
source_candidates=0
artifact_download_attempts=0
pdf_document_files=0
xml_document_files=0
raw_api_response_document_files=42
```

## Limitations

- The MVP uses the Opendatasoft API as primary discovery and does not cross-check
  HTML summary pages at runtime.
- The API currently returns `http://` artifact URLs that redirect to `https://`;
  the adapter preserves the official API URL values as returned.
- Pagination beyond `limit=100` is not implemented because the sampled dates are
  below that threshold. A 30-day backfill task should add a completeness guard if
  any date exceeds the limit.
- No XML/PDF/HTML artifacts are downloaded or parsed.
- No candidate extraction exists for BOCYL.

## Next Recommended Task

```text
TASK-AUTO-BOCYL-003 - Controlled BOCYL 30-day metadata backfill
```

Required guardrails:

- metadata-only;
- one source only;
- backup before/after if run against persistent DB;
- no candidates;
- no artifact downloads;
- no downstream writes;
- stop on API/parser/storage failures.

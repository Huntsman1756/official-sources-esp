# BOPV/EHAA Adapter MVP Local - 2026-05-23

## Scope

Implemented a local metadata-only BOPV/EHAA adapter for one explicit publication
date.

Out of scope and not performed:

- no VPS access;
- no historical backfill;
- no candidate creation;
- no downstream writes;
- no MCP exposure;
- no PDF artifact download.

## Implemented Endpoints

The adapter uses official BOPV/EHAA URLs under `https://www.euskadi.eus`.

| Purpose | Pattern |
| --- | --- |
| Monthly calendar | `https://www.euskadi.eus/bopv2/datos/MMYYYY.shtml` |
| Issue HTML | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.shtml` |
| Issue XML | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.xml` |
| Document HTML | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.shtml` |
| Document XML | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.xml` |
| Document PDF URL metadata | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.pdf` |
| Document EPUB URL metadata | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.epub` |

Safe confirmation probes were run for:

- `GET https://www.euskadi.eus/bopv2/datos/052026.shtml` -> `200`, `text/html; charset=ISO-8859-1`;
- `GET https://www.euskadi.eus/bopv2/datos/2026/05/s26_0093.xml` -> `200`, `application/xml`, `10643` bytes;
- `GET https://www.euskadi.eus/bopv2/datos/2026/05/2602104a.xml` -> `200`, `application/xml`, `2436` bytes;
- `HEAD https://www.euskadi.eus/bopv2/datos/2026/05/2602104a.pdf` -> `200`, `application/pdf`, `132273` bytes.

The PDF check used `HEAD` only. No PDF body was downloaded or stored.

## Adapter Behavior

CLI:

```text
official-sources ingest-bopv-date --date YYYY-MM-DD
```

Flow:

1. Validate `YYYY-MM-DD`.
2. Fetch the month calendar.
3. Parse `diasHabilitados` and `enlaces` arrays.
4. If the target date is absent or has no issue link, finish the ingestion run as
   `no_publication`.
5. Fetch issue XML for each issue link on the date.
6. Parse document order, title, section, subsection and organism metadata.
7. Preserve official HTML/XML/PDF/EPUB URLs as metadata.
8. Store raw calendar+issue payload hash as `source_snapshot_hash`.
9. Store documents and `raw_api_response` integrity rows only.

Stable identifiers:

- issue: `BOPV-YYYY-NNNN`, for example `BOPV-2026-0093`;
- document: `BOPV-YYYY-MM-YYNNNNa`, for example `BOPV-2026-05-2602104a`;
- external id: `BOPV:BOPV-YYYY-MM-YYNNNNa`.

Source registry entry:

```text
code=BOPV
name=Boletín Oficial del País Vasco / Euskal Herriko Agintaritzaren Aldizkaria
jurisdiction=autonomous
region_code=ES-PV
base_url=https://www.euskadi.eus/bopv2/datos
access_type=official_xml
reliability_level=canonical
```

## Fixtures And Tests

Added fixtures:

- `bopv_calendar_052026.html`;
- `bopv_calendar_no_publication.html`;
- `bopv_issue_s26_0093.xml`;
- `bopv_document_2602104a.xml`.

Added tests for:

- date validation;
- source record creation;
- date-to-issue calendar parsing;
- no-publication behavior;
- issue XML document parsing;
- document XML metadata parsing;
- official URL preservation;
- raw payload hash preservation;
- citation generation;
- no PDF file storage;
- no source candidate creation;
- CLI success and no-publication paths.

## Local Smoke

One-date local temp DB smoke:

```text
official-sources ingest-bopv-date --date 2026-05-20
```

Result:

```text
status=success
issue_identifier=BOPV-2026-0093
documents_fetched=25
documents_new=25
documents_updated=0
pdf_files=0
candidates=0
```

No backfill was run.

## Risks

- Calendar parsing depends on official JavaScript array names
  `diasHabilitados` and `enlaces`.
- The adapter allows multiple issues for a single date, but only one real-date
  smoke was performed.
- Document stems are derived from publication year plus zero-padded official
  order number and suffix `a`; this matches the sampled BOPV issue/document URL
  pattern.
- Encoding remains mixed: calendar HTML is ISO-8859-1, while issue/document XML
  advertises UTF-8.

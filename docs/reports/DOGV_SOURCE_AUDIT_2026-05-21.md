# DOGV Source Audit

Date: 2026-05-21

## Objective

Assess DOGV / Diari Oficial de la Generalitat Valenciana as a possible next autonomous source for `official-sources`.

This was research only. No adapter was implemented, no database was touched, no candidates were created, no PDFs were downloaded in bulk, and no downstream project was touched.

## Context

BOJA is validated and closed as the first autonomous metadata-first source. BOCM has a metadata adapter MVP, but its 30-day metadata backfill is paused because `2026-05-06` repeatedly fails from the VPS while the main site remains reachable.

DOGV was audited as a clean next autonomous source candidate.

## Official URLs Inspected

- `https://dogv.gva.es/`
- `https://dogv.gva.es/es/inici/`
- `https://dogv.gva.es/dogv-portal-frontend/es`
- `https://dogv.gva.es/dogv-portal/dogv?date=YYYY-MM-DD&lang=es`
- `https://dogv.gva.es/dogv-portal/dogv/calendar?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`
- `https://dogv.gva.es/dogv-portal/disposicion/metadata/{id}?lang=es`
- `https://dogv.gva.es/dogv-portal/export/disposicion/xml/dinamico/{id}?lang=es`
- `https://dogv.gva.es/dogv-portal/export/disposicion/{id}/pdf?lang=es`
- `https://dogv.gva.es/datos/YYYY/MM/DD/pdf/<document>.pdf`
- `https://dogv.gva.es/es/resultat-dogv?signatura=YYYY/NNNNN`
- `https://dogv.gva.es/es/disposicio?sig=YYYY/NNNNN`
- `https://dogv.gva.es/es/preguntes-frequents`
- `https://dogv.gva.es/es/projecte-eli-identificador-legislatiu-europeu`
- `https://dogv.gva.es/robots.txt`
- `https://dogv.gva.es/sitemap.xml`

## Endpoint Findings

The public Liferay page embeds an Angular frontend served from:

```text
https://dogv.gva.es/dogv-portal-frontend/es
```

The frontend uses an official backend base:

```text
https://dogv.gva.es/dogv-portal
```

Relevant backend routes observed from the frontend bundle:

```text
GET  /dogv?date=YYYY-MM-DD&lang=es
GET  /dogv/latest?lang=es
GET  /dogv/calendar?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
POST /dogv/search?lang=es&page=N&size=10&sort=<sort>
GET  /dogv/{id}/versionesSumario?lang=es
GET  /dogv/{id}?ordenSumario=<order>&lang=es
GET  /dogv/anteriorYSiguiente?date=YYYY-MM-DD&lang=es
GET  /dogv/obtenerIdDogv/{codigoInsercion}
GET  /disposicion/metadata/{id}?lang=es
GET  /export/disposicion/xml/dinamico/{id}?lang=es
GET  /export/disposicion/{id}/pdf?lang=es
GET  /export/dogvCompleto/{numDogv}/pdf?lang=es
GET  /export/sumario/{numDogv}/pdf?lang=es
```

No formal OpenAPI document was found during this audit, but the frontend-backed JSON endpoints are stable enough for an MVP probe.

## Tested Dates

| Date | HTTP | DOGV issue number | Documents | Summary PDF | Result |
| --- | ---: | ---: | ---: | --- | --- |
| 2026-05-20 | 200 | 10366 | 49 | `/2026/05/20/pdf/sumario_2026_10366_es.pdf` | publication |
| 2026-05-19 | 200 | 10365 | 44 | `/2026/05/19/pdf/sumario_2026_10365_es.pdf` | publication |
| 2026-05-18 | 200 | 10364 | 70 | `/2026/05/18/pdf/sumario_2026_10364_es.pdf` | publication |
| 2026-05-17 | 200 | null | 0 | null | no publication |

The no-publication date returned a JSON object with null `cabecera`, null `disposiciones`, null `fechaSumario`, and null `urlPdf`. The monthly calendar endpoint also omitted `2026-05-17`.

## Date-To-Issue Strategy

Recommended primary strategy:

```text
GET /dogv?date=YYYY-MM-DD&lang=es
```

If the response contains `cabecera.numeroDogv`, that number is the issue identifier for the date.

Recommended fallback/check:

```text
GET /dogv/calendar?startDate=YYYY-MM-01&endDate=YYYY-MM-last
```

The calendar endpoint returns publication dates for a month and includes `esBis`, which matters because DOGV can publish duplicate/special issue dates.

No-publication behavior:

```text
HTTP 200 with null cabecera/disposiciones/urlPdf
or date absent from /dogv/calendar
```

Do not infer no-publication from weekends alone. The official FAQ says DOGV normally does not publish on Saturdays, Sundays, and holidays, but extraordinary publication is possible.

## Document Metadata And Evidence Formats

The date endpoint returns document-level metadata suitable for metadata-only ingestion:

```text
id
titulo
seccion.id / seccion.descripcion
subseccion.id / subseccion.descripcion
paginaInicial
organismo
fechaPublicacion
codigoInsercion
urlPdf
```

Observed identifier candidates:

- Backend numeric ID: example `477348`.
- DOGV insertion code: example `2026/16061`.
- Official metadata identifier: example `DOGV-C-2026-16061`.

Recommended `official_identifier`:

```text
DOGV-C-YYYY-NNNNN
```

Fallback if metadata lookup is unavailable:

```text
DOGV:YYYY/NNNNN
```

Canonical document URL candidate:

```text
https://dogv.gva.es/es/resultat-dogv?signatura=YYYY/NNNNN
```

Alternative frontend route:

```text
https://dogv.gva.es/es/disposicio?sig=YYYY/NNNNN
```

Evidence formats observed:

| Format | Availability | Example pattern | Notes |
| --- | --- | --- | --- |
| JSON date metadata | yes | `/dogv-portal/dogv?date=YYYY-MM-DD&lang=es` | Best MVP source for issue and document list. |
| JSON document metadata | yes | `/dogv-portal/disposicion/metadata/{id}?lang=es` | Includes identifier, journal number, publication date, titles, HTML body, and text metadata. |
| XML-like dynamic export | yes | `/dogv-portal/export/disposicion/xml/dinamico/{id}?lang=es` | Returns a text/plain XML-like document with metadata and escaped HTML text. |
| PDF document | yes | `/datos/YYYY/MM/DD/pdf/YYYY_NNNNN_es.pdf` | Direct official PDF path returned by metadata. Do not download by default. |
| Summary PDF | yes | `/datos/YYYY/MM/DD/pdf/sumario_YYYY_NNNNN_es.pdf` | Available per issue. Do not download by default. |
| HTML public page | yes | `/es/resultat-dogv?signatura=YYYY/NNNNN` | Liferay page with embedded frontend behavior. |
| RSS | not confirmed | not found | Do not rely on RSS for MVP. |
| OpenAPI | not found | not found | Use observed official backend endpoints with fixtures. |

The `/export/disposicion/{id}/pdf` route returned a short path string, not the PDF bytes, in the probe. The direct `/datos/...pdf` URL returned `application/pdf` and a normal content length via HEAD.

## Citation Feasibility

DOGV can support citation metadata with:

```text
source_code: DOGV
source_name: Diari Oficial de la Generalitat Valenciana
official_identifier: DOGV-C-YYYY-NNNNN
title: document title from DOGV metadata
official_url: https://dogv.gva.es/es/resultat-dogv?signatura=YYYY/NNNNN
publication_date: YYYY-MM-DD
journal_number: cabecera.numeroDogv
section/subsection: DOGV section metadata
```

The raw date JSON and raw document metadata JSON are suitable hash inputs. Hash raw official payload bytes before parsing, not normalized fields.

## MVP Adapter Shape

Recommended MVP scope:

```text
official-sources ingest-dogv-date --date YYYY-MM-DD
```

Behavior:

1. Validate date.
2. Fetch `/dogv?date=YYYY-MM-DD&lang=es`.
3. If response has null `cabecera` and null `disposiciones`, record `no_publication`.
4. Store issue metadata using `cabecera.numeroDogv`.
5. Store one `official_documents` row per `disposiciones[]` item.
6. Preserve public document URL, direct PDF URL, document metadata URL, and dynamic XML URL as metadata/document file references.
7. Hash the raw date JSON response before parsing.
8. Optionally fetch document metadata JSON for each document in a small date-only MVP if request count is acceptable.
9. Do not download PDFs.
10. Do not create candidates.
11. Do not write downstream.

Suggested source record:

```text
code = DOGV
name = Diari Oficial de la Generalitat Valenciana
jurisdiction = autonomous
region_code = ES-VC
access_type = official_json
reliability_level = canonical
```

## Risks

- No formal OpenAPI was found; endpoint contracts are inferred from the official frontend.
- DOGV is a Liferay/Angular portal; frontend bundle route names can change.
- Encoding must be tested carefully. Some console probes displayed mojibake, although JSON content is served as UTF-8.
- Special issues need explicit handling through `esBis` and summary versions.
- The `/dogv?date=` endpoint returns `200` for no-publication dates, so null response shape must be tested explicitly.
- The direct PDF URLs are stable, but PDFs must remain out of scope for a metadata MVP.
- XML dynamic export is useful, but the standard XML export returned `{}` for the sampled document; use dynamic XML or metadata JSON in the MVP.
- Robots policy should be reviewed before any artifact download task. This audit did not crawl or bulk download.

## Complexity And Priority

Complexity: `low-medium`

Priority: `P1`

DOGV appears easier than BOCM for the initial metadata MVP because date-to-issue resolution is a direct JSON request instead of an HTML form/search discovery process. It is still more fragile than BOJA because no formal OpenAPI was found.

## Recommendation

Start `TASK-AUTO-DOGV-002 - DOGV metadata adapter MVP`.

Keep the MVP metadata-only:

```text
date -> DOGV issue JSON
issue -> document list
document metadata normalization
official URL preservation
direct PDF/XML/metadata URL preservation only
raw payload hash
ingestion_run
no candidates
no PDFs
no downstream
```

Do not move to candidate extraction until a controlled metadata-only backfill is complete and validated.

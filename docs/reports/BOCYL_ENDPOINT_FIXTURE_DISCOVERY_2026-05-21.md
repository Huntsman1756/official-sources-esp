# BOCYL Endpoint Fixture Discovery - 2026-05-21

## Scope

This report documents the minimum official BOCYL endpoints and fixtures needed
for a future metadata adapter MVP.

This was research/probe only:

- no adapter was implemented;
- no database was touched;
- no candidates were created;
- no bulk PDFs were downloaded;
- no backfills were run;
- no VPS was touched;
- no EduAyudas or `la-ayuda` work was performed;
- no MCP surface was exposed.

Only a few safe official HTTP probes were performed.

## Executive Summary

BOCYL is ready for a metadata-only MVP after this fixture discovery.

Recommended MVP posture:

```text
complexity: low
start MVP: yes
primary discovery: official JCyL Opendatasoft API
canonical document id: BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ
raw metadata hash: exact API JSON response and/or official XML bytes
PDF behavior: store URL only by default; fetch PDF only for scoped artifact checks
```

The strongest route is to use the official open-data API for date-scoped
document discovery, then keep the official BOCYL HTML summary page as a
cross-check and the official XML/HTML/PDF links as artifact URLs.

## Official URLs Found

| Purpose | URL |
| --- | --- |
| BOCYL portal | <https://bocyl.jcyl.es/portada.do> |
| Issue by date | `https://bocyl.jcyl.es/boletin.do?fechaBoletin=DD%2FMM%2FYYYY` |
| Example issue by date | <https://bocyl.jcyl.es/boletin.do?fechaBoletin=20%2F05%2F2026> |
| RSS index | <https://bocyl.jcyl.es/indiceRss.do> |
| Complete RSS feed | <https://bocyl.jcyl.es/rss.do> |
| Official dataset explorer | <https://jcyl.opendatasoft.com/explore/dataset/bocyl/> |
| Official API records endpoint | <https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl/records> |
| Datos.gob.es dataset entry | <https://datos.gob.es/es/catalogo/a07002862-boletin-oficial-de-castilla-y-leon-bocyl1> |

The BOCYL portal exposes calendar navigation, access by exact date, RSS, and
the open-data link. The official open-data dataset is identified as `bocyl` and
contains BOCYL dispositions.

## Endpoint Behavior

### Official API

Base endpoint:

```text
https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl/records
```

Useful date filter:

```text
?limit=100&where=fecha_publicacion=date'YYYY-MM-DD'
```

Observed fields in a sampled record:

```text
no_edicion
fecha_publicacion
seccion
subseccion
apartado
organismo
suborganismo
rango
titulo
pagina_inicial
pagina_final
enlace_fichero_pdf
enlace_fichero_xml
enlace_fichero_html
```

Sample API record for `2026-05-20`:

```text
no_edicion: 94/2026
fecha_publicacion: 2026-05-20
document id from artifact links: BOCYL-D-20052026-94-1
pdf: http://bocyl.jcyl.es/boletines/2026/05/20/pdf/BOCYL-D-20052026-94-1.pdf
xml: http://bocyl.jcyl.es/boletines/2026/05/20/xml/BOCYL-D-20052026-94-1.xml
html: http://bocyl.jcyl.es/html/2026/05/20/html/BOCYL-D-20052026-94-1.do
```

### Issue HTML by Date

Pattern:

```text
https://bocyl.jcyl.es/boletin.do?fechaBoletin=DD%2FMM%2FYYYY
```

For publication dates, the page returns `text/html;charset=UTF-8` and includes
the breadcrumb date, issue heading, and repeated `BOCYL-D-*` artifact IDs.

For `2026-05-20`, the page included:

```text
BOCYL: 20 de mayo de 2026
Sumario BOCYL n? 94/2026
BOCYL-D-20052026-94-1
```

The rendered `n?` is an encoding artifact in the console capture for `nº`; the
issue identifier is still unambiguous from the API `no_edicion` and the
document IDs.

For a no-publication date such as Sunday `2026-05-17`, the endpoint returned
HTTP 200 and the portal shell, but no issue heading and no date-specific
document IDs. Therefore, no-publication detection should not rely on HTTP
status alone.

### Artifact URLs

For `BOCYL-D-20052026-94-1`, targeted HEAD checks showed:

| Format | URL pattern | Response |
| --- | --- | --- |
| XML | `/boletines/YYYY/MM/DD/xml/BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ.xml` | `200`, `application/xml`, content length `8534` |
| HTML | `/html/YYYY/MM/DD/html/BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ.do` | `200`, `text/html;charset=UTF-8` |
| PDF | `/boletines/YYYY/MM/DD/pdf/BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ.pdf` | `200`, `application/pdf`, content length `1001213` |

The API currently returns `http://` artifact links. Targeted checks redirected
to `https://` successfully. The MVP should preserve the official URL as
returned and may also store the final resolved HTTPS URL.

### RSS

The RSS index is available at:

```text
https://bocyl.jcyl.es/indiceRss.do
```

It lists:

```text
rss.do
rss.do?seccion=I
rss.do?seccion=II
rss.do?seccion=III
rss.do?seccion=IV
rss.do?seccion=V
```

The complete feed `https://bocyl.jcyl.es/rss.do` returned `200` with
`text/xml;charset=UTF-8`.

RSS is useful for freshness monitoring, but the API should be the primary
metadata discovery surface for the MVP.

## Tested Dates

| Date | Status | Issue identifier | Issue URL | Document count | No-publication behavior | Raw response type |
| --- | --- | --- | --- | ---: | --- | --- |
| 2026-05-20 | published | `94/2026` | <https://bocyl.jcyl.es/boletin.do?fechaBoletin=20%2F05%2F2026> | API `42`; HTML saw `43` unique `BOCYL-D-*` tokens because page chrome includes the service charter PDF id | Publication page returns HTTP 200 with issue summary and document IDs | API JSON; issue HTML `text/html;charset=UTF-8` |
| 2026-05-19 | published | `93/2026` | <https://bocyl.jcyl.es/boletin.do?fechaBoletin=19%2F05%2F2026> | API `40`; HTML saw `41` unique tokens for the same page-chrome reason | Publication page returns HTTP 200 with issue summary and document IDs | API JSON; issue HTML `text/html;charset=UTF-8` |
| 2026-05-18 | published | `92/2026` | <https://bocyl.jcyl.es/boletin.do?fechaBoletin=18%2F05%2F2026> | API `44`; HTML saw `45` unique tokens for the same page-chrome reason | Publication page returns HTTP 200 with issue summary and document IDs | API JSON; issue HTML `text/html;charset=UTF-8` |
| 2026-05-17 | no publication observed | none | <https://bocyl.jcyl.es/boletin.do?fechaBoletin=17%2F05%2F2026> | API `0`; HTML only exposed non-date-specific page chrome | HTTP 200 portal shell without issue heading/date-specific `BOCYL-D-17052026-*` IDs | API JSON with zero results; portal HTML shell |

The extra HTML token observed on publication pages was
`BOCYL-D-18112022-30`, linked from the page footer as the BOCYL service charter.
Therefore, document counts should come from the API or from scoped parsing of
the issue content area, not from a whole-page regex over the HTML shell.

## Stable Identifier Strategy

Issue identifier:

```text
source_code = BOCYL
issue_id = no_edicion + fecha_publicacion
example = 94/2026 @ 2026-05-20
```

Document identifier:

```text
document_id = BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ
example = BOCYL-D-20052026-94-1
```

This document identifier appears in PDF, XML, and HTML artifact URLs, so it is
the best canonical document key for the MVP.

Official URL strategy:

```text
issue_url = https://bocyl.jcyl.es/boletin.do?fechaBoletin=DD%2FMM%2FYYYY
pdf_url = enlace_fichero_pdf
xml_url = enlace_fichero_xml
html_url = enlace_fichero_html
```

Store artifact URLs exactly as returned by the API. Store final resolved URLs
only as secondary fetch metadata if the HTTP client follows the `http` to
`https` redirect.

## Fixture Candidates

Use these small fixtures for a future MVP design:

| Fixture | Purpose |
| --- | --- |
| API date `2026-05-20` | Normal publication day with `94/2026` and 42 API records. |
| API date `2026-05-19` | Adjacent publication day with `93/2026` and 40 API records. |
| API date `2026-05-18` | Adjacent publication day with `92/2026` and 44 API records. |
| API date `2026-05-17` | No-publication date with zero API records and HTML shell only. |
| Document `BOCYL-D-20052026-94-1` | Verify XML/HTML/PDF artifact URL behavior and identifier extraction. |
| RSS `rss.do` | Freshness monitor fixture, not canonical discovery. |

No fixture files were saved in this task; the report records the minimal fixture
coordinates.

## MVP Adapter Recommendation

Start `TASK-AUTO-BOCYL-002 - BOCYL metadata adapter MVP`.

Recommended MVP flow:

1. Accept an explicit date.
2. Query the official API with `fecha_publicacion=date'YYYY-MM-DD'`.
3. If `total_count == 0`, record no publication for that date.
4. If records exist, group by `no_edicion` and `fecha_publicacion`.
5. Extract document metadata and `BOCYL-D-*` from artifact URLs.
6. Store API raw JSON hash for the date query.
7. Store XML/HTML/PDF URLs without fetching PDFs by default.
8. Optionally fetch one XML artifact per fixture during tests to validate raw
   artifact hashing.

The issue HTML page should be used as a cross-check and fallback, not as the
primary document counter.

## Risks

- The API can lag the public issue page on same-day publication; MVP should
  include a clear retry/freshness policy.
- API artifact URLs currently use `http://` and redirect to `https://`; preserve
  source URLs and record resolved URLs separately.
- Whole-page HTML parsing overcounts because the site shell includes unrelated
  BOCYL document IDs.
- Historical coverage may differ from current records; first MVP should use
  recent explicit dates only.
- RSS is useful for alerts but should not be treated as the source of record.

## Next Task

```text
TASK-AUTO-BOCYL-002 - BOCYL metadata adapter MVP
```

Scope for that task should remain metadata-only:

- no candidates;
- no PDF bulk downloads;
- no backfills;
- no downstream writes;
- no VPS deployment unless separately requested.

# BOPV/EHAA Endpoint Fixture Discovery - 2026-05-21

## Scope

This report documents the minimum official BOPV/EHAA endpoints and fixtures
needed for a future metadata adapter MVP.

This was research/probe only:

- no adapter was implemented;
- no database was touched;
- no candidates were created;
- no bulk PDFs were downloaded;
- no downstream work was performed;
- no VPS was touched.

Only a few safe official HTTP probes were performed.

## Executive Summary

BOPV/EHAA can start a metadata-only MVP.

Recommended MVP posture:

```text
complexity: medium
start MVP: yes
primary discovery: official monthly calendar + issue XML/HTML summary
secondary metadata: official Open Data Euskadi BOPV API
canonical issue id: BOPV-YYYY-ISSUE_NUMBER
canonical document id: YYNNNNa from official artifact stem, plus full order number
raw metadata hash: exact issue XML bytes and/or exact document XML bytes
PDF behavior: store URL only by default; fetch PDF only for scoped artifact checks
```

The strongest route is to use the official calendar file to map a publication
date to the issue summary URL, then parse the issue XML or HTML for complete
document ordering. The Open Data Euskadi API is useful JSON metadata, but it is
not a full replacement for the issue summary because the exposed
`/bopv/administrative-acts` resource did not match the full sumario counts in
the sampled issue pages.

## Official URLs Found

| Purpose | URL |
| --- | --- |
| BOPV portal / latest issue | <https://www.euskadi.eus/web01-bopv/es/bopv2/datos/Ultimo.shtml> |
| Direct latest issue shell | <https://www.euskadi.eus/bopv2/datos/Ultimo.shtml> |
| Current/latest calendar | <https://www.euskadi.eus/bopv2/datos/CalUltimo.shtml> |
| Month calendar pattern | `https://www.euskadi.eus/bopv2/datos/MMYYYY.shtml` |
| May 2026 calendar | <https://www.euskadi.eus/bopv2/datos/052026.shtml> |
| Issue summary pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.shtml` |
| Issue XML pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.xml` |
| Full issue PDF pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.pdf` |
| Document HTML pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.shtml` |
| Document XML pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.xml` |
| Document PDF pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.pdf` |
| Document EPUB pattern | `https://www.euskadi.eus/bopv2/datos/YYYY/MM/YYNNNNa.epub` |
| Latest RSS/XML | <https://www.euskadi.eus/bopv2/datos/Ultimo.xml> |
| Open Data API docs | <https://opendata.euskadi.eus/api-bopv/?api=bopv> |
| OpenAPI descriptor | <https://opendata.euskadi.eus/contenidos/recurso_tecnico/data_apirest/es_def/adjuntos/bopv.json> |
| API base | <https://api.euskadi.eus/bopv/administrative-acts> |

The same issue and document resources are also reachable under the
`/web01-bopv/es/` portal prefix. The shorter `/bopv2/datos/...` URLs returned
the raw issue/document resources directly and are suitable as fixture
coordinates.

## Endpoint Behavior

### Date-to-Issue Calendar

The month calendar endpoint is:

```text
https://www.euskadi.eus/bopv2/datos/MMYYYY.shtml
```

For May 2026 it returned `text/html; charset=ISO-8859-1` with JavaScript arrays:

```text
diasHabilitados = ['20260504', ..., '20260518', '20260519', '20260520', ...]
enlaces = [..., ['s26_0091.shtml'], ['s26_0092.shtml'], ['s26_0093.shtml'], ...]
asuntos = [..., '2602076', '2602103', '2602128', ...]
```

This gives a deterministic date-to-issue mapping without guessing issue
numbers. For `2026-05-17`, the date is absent from `diasHabilitados`, which is
the clean no-publication signal observed in this probe.

### Issue Summary

Issue summary pattern:

```text
https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.shtml
```

For example:

```text
https://www.euskadi.eus/bopv2/datos/2026/05/s26_0093.shtml
```

The issue summary returned `200` with `text/html; charset=ISO-8859-1` and
included:

```text
Sumario n. 93, miercoles 20 de mayo de 2026
```

Document rows expose:

```text
BOPVSumarioSeccion
BOPVSumarioSubseccion
BOPVSumarioOrganismo
BOPVSumarioTitulo
BOPVSumarioOrden
```

The issue XML endpoint:

```text
https://www.euskadi.eus/bopv2/datos/2026/05/s26_0093.xml
```

returned `200`, `application/xml`, length `10643`, and exposed the same summary
metadata with `BOPVSumarioOrden` values. This should be the preferred fixture
for issue-level document discovery.

### Document Detail and Artifacts

Sample document from issue 93:

```text
order: 2104
html: https://www.euskadi.eus/bopv2/datos/2026/05/2602104a.shtml
xml:  https://www.euskadi.eus/bopv2/datos/2026/05/2602104a.xml
pdf:  https://www.euskadi.eus/bopv2/datos/2026/05/2602104a.pdf
epub: https://www.euskadi.eus/bopv2/datos/2026/05/2602104a.epub
```

Targeted HEAD checks showed:

| Format | Response |
| --- | --- |
| HTML | `200`, `text/html; charset=ISO-8859-1` |
| XML | `200`, `application/xml`, content length `2436` |
| PDF | `200`, `application/pdf`, content length `132273` |
| EPUB | `200`, `application/epub+zip`, content length `120551` |

The document XML contains a compact official metadata/body structure:

```text
DOCUMENTO NEXPEI
BOPVSeccion
BOPVSubseccion
BOPVOrganismo
BOPVOrden
BOPVTitulo
BOPVDetalle
BOPVClave
BOPVFirma...
```

This makes document XML a good raw fixture for citation text and hashing. The
PDF should remain an artifact URL unless a later task explicitly asks for
scoped evidence downloads.

### JSON/API

The official OpenAPI descriptor is:

```text
https://opendata.euskadi.eus/contenidos/recurso_tecnico/data_apirest/es_def/adjuntos/bopv.json
```

It defines:

```text
GET /bopv/administrative-acts
GET /bopv/administrative-acts/{year}
GET /bopv/administrative-acts/{year}/{month}
GET /bopv/administrative-acts/{year}/{month}/{num-order}
```

The API server is:

```text
https://api.euskadi.eus
```

Example:

```text
https://api.euskadi.eus/bopv/administrative-acts/2026/5?itemsOfPage=10&currentPage=1&lang=SPANISH
```

Observed response:

```text
200 application/json
totalItems: 234
totalPages: 24
```

API records include stable useful fields such as:

```text
id
name
publishDate
numBulletin
numOrder
normativeRange
department
section
mainEntityOfPage
downloadable[]
_links.self.href
```

Important caveat: in this probe, API counts grouped by publication timestamp
did not equal the complete issue summary counts from `s26_*.xml`/`.shtml`.
Treat the API as enrichment/JSON metadata, not as the sole issue inventory,
until a future adapter proves exact parity.

### RSS

The latest feed:

```text
https://www.euskadi.eus/bopv2/datos/Ultimo.xml
```

returned `200`, `application/xml`, and RSS 2.0 content for the latest issue
observed at probe time:

```text
Boletin N. 95, fecha 22/05/2026
```

RSS is suitable for freshness monitoring and latest-issue checks. It is not a
date-scoped discovery endpoint for historical fixtures.

## Tested Dates

Calendar and issue summary evidence:

| Date | Status | Issue identifier | Issue URL | Document count | No-publication behavior | Raw response type |
| --- | --- | --- | --- | ---: | --- | --- |
| 2026-05-20 | published | `93` / `s26_0093` | <https://www.euskadi.eus/bopv2/datos/2026/05/s26_0093.shtml> | `25` from `BOPVSumarioOrden` in HTML/XML | Date present in May calendar `diasHabilitados`; issue summary and issue XML return 200 | Calendar HTML; issue HTML `text/html; charset=ISO-8859-1`; issue XML `application/xml` |
| 2026-05-19 | published | `92` / `s26_0092` | <https://www.euskadi.eus/bopv2/datos/2026/05/s26_0092.shtml> | `27` from `BOPVSumarioOrden` in HTML | Date present in May calendar; issue summary returns 200 | Calendar HTML; issue HTML `text/html; charset=ISO-8859-1` |
| 2026-05-18 | published | `91` / `s26_0091` | <https://www.euskadi.eus/bopv2/datos/2026/05/s26_0091.shtml> | `30` from `BOPVSumarioOrden` in HTML | Date present in May calendar; issue summary returns 200 | Calendar HTML; issue HTML `text/html; charset=ISO-8859-1` |
| 2026-05-17 | no publication observed | none | none from calendar | `0` | Date absent from May calendar `diasHabilitados`; no issue link to fetch | Calendar HTML `text/html; charset=ISO-8859-1` |

Adjacent control: `2026-05-15` maps to issue `90` / `s26_0090` and returned
`20` summary orders. `2026-05-17` is therefore a normal weekend gap between
published issues rather than an HTTP failure.

## Stable Identifier Strategy

Issue identifier:

```text
source_code = BOPV
issue_id = BOPV-YYYY-NNNN
example = BOPV-2026-0093
```

Issue URL:

```text
https://www.euskadi.eus/bopv2/datos/YYYY/MM/sYY_NNNN.shtml
```

Document identifier:

```text
document_stem = YYNNNNa
order_number = NNNN from BOPVSumarioOrden / BOPVOrden
document_id = BOPV-YYYY-MM-YYNNNNa
example = BOPV-2026-05-2602104a
```

The document stem is embedded in HTML/XML/PDF/EPUB URLs. The order number is
also present in issue XML and document XML. Store both; use the URL stem for
artifact identity and the BOPV order number for human citation.

## Document Metadata Strategy

Recommended MVP flow:

1. Accept an explicit publication date.
2. Fetch `MMYYYY.shtml` calendar for the date's month.
3. If the date is absent from `diasHabilitados`, record no publication for that
   date.
4. If present, map the date position to the corresponding `sYY_NNNN.shtml`
   issue path.
5. Fetch the issue XML `sYY_NNNN.xml` as the primary summary fixture.
6. Extract issue number, document order, section, subsection, organism, title,
   and document stems.
7. Build document HTML/XML/PDF/EPUB URLs from the official stem pattern.
8. Optionally fetch document XML for scoped metadata/body hashing.
9. Store PDF URLs but do not fetch PDFs by default.
10. Use the Open Data API only as enrichment and cross-check metadata until
    parity with complete issue inventories is proven.

## Evidence Formats

| Evidence | Availability | Recommended use |
| --- | --- | --- |
| Monthly calendar HTML | Available as `MMYYYY.shtml` | Date-to-issue mapping and no-publication detection |
| Issue HTML | Available as `sYY_NNNN.shtml` | Human-readable cross-check and fallback parser |
| Issue XML | Available as `sYY_NNNN.xml` | Primary issue fixture and document list |
| Full issue PDF | Available as `sYY_NNNN.pdf` | Artifact URL only; scoped checks if needed |
| Document HTML | Available as `YYNNNNa.shtml` | Human-readable citation URL |
| Document XML | Available as `YYNNNNa.xml` | Primary document text/hash fixture |
| Document PDF | Available as `YYNNNNa.pdf` | Artifact URL only by default |
| Document EPUB | Available as `YYNNNNa.epub` | Optional alternate artifact |
| Latest RSS/XML | Available as `Ultimo.xml` | Freshness monitor only |
| Open Data JSON API | Available under `api.euskadi.eus` | Enrichment/cross-check; not sole inventory |

## Fixture Candidates

Use these small fixture coordinates for a future MVP:

| Fixture | Purpose |
| --- | --- |
| Calendar `052026.shtml` | Date-to-issue mapping and no-publication behavior. |
| Issue `s26_0093.xml` | Normal publication day, `2026-05-20`, 25 documents. |
| Issue `s26_0092.xml` | Adjacent publication day, `2026-05-19`, 27 documents. |
| Issue `s26_0091.xml` | Adjacent publication day, `2026-05-18`, 30 documents. |
| No-publication date `2026-05-17` | Date absent from calendar arrays. |
| Document `2602104a.xml` | Small document XML fixture from issue 93. |
| Document `2602104a.shtml` | HTML detail/citation fixture. |
| Document `2602104a.pdf` | PDF URL availability check only. |
| API month `2026/5` | JSON enrichment and count-parity guard. |
| `Ultimo.xml` | RSS/freshness fixture. |

No fixture files were saved in this task; the report records the minimal fixture
coordinates.

## MVP Adapter Recommendation

Start a BOPV/EHAA metadata-only MVP.

Recommended next task:

```text
TASK-AUTO-BOPV-002 - BOPV/EHAA metadata adapter MVP
```

Scope should remain metadata/index-only:

- no candidates;
- no PDF bulk downloads;
- no downstream writes;
- no VPS deployment;
- no historical backfill beyond explicit fixture dates unless separately
  approved.

## Risks

- Encoding is legacy `ISO-8859-1` on many BOPV pages; parsers must decode
  explicitly and preserve raw bytes for hashing.
- The calendar stores date and link arrays in JavaScript, so date-to-issue
  parsing needs a small robust parser rather than plain link scraping.
- The first May 2026 calendar entry maps one date to two issue links
  (`s26_0080.shtml`, `s26_0081.shtml`), so the MVP must allow multiple issues
  for one date even if the sampled target dates have one issue each.
- Open Data API `publishDate` is UTC-like (`T22:00:00Z`) and can look one day
  earlier than the local issue date; do not infer local publication date from
  API timestamp without normalization.
- Open Data API inventory did not match full issue summary counts in this
  probe. It should not be the primary document counter until parity is proven.
- RSS only exposes the latest issue and should not replace date-scoped
  discovery.

## Complexity

```text
metadata MVP complexity: medium
reason: official issue XML and document XML are stable, but date-to-issue
        requires parsing calendar JavaScript arrays and allowing multi-issue
        dates.
```

The MVP is feasible because publication/no-publication behavior can be detected
without search forms, and complete document lists are available in compact
official XML.

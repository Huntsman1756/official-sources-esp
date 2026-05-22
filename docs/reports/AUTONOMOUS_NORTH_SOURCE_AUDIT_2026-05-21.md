# Northern Autonomous Bulletin Source Audit - 2026-05-21

## Scope

This report audits five northern autonomous bulletin sources as possible future
`official-sources` inputs:

- DOGC Catalunya
- BOA Aragon
- BON Navarra
- BOPV/EHAA Pais Vasco
- BOR La Rioja

This was research only:

- no VPS was touched;
- no database was touched;
- no candidates were created;
- no adapters were implemented;
- no backfills were run;
- no downstream projects were touched;
- no bulk PDF downloads or crawling were run.

The checks were limited to official web sources and a few safe, targeted HTTP
metadata/HTML checks.

## Executive Summary

Recommended first northern sources:

```text
P1 - BOPV/EHAA: official OpenAPI/JSON surface, stable order IDs, direct artifacts.
P1 - BOR: official XML API and explicit no-publication behavior.
```

DOGC is structurally strong because it has official CVE identifiers and HTML, PDF,
XML Akoma Ntoso, RDF and Turtle formats. It should not be the first northern MVP
until its date-to-summary and REST/format endpoints are pinned with fixtures.

BOA and BON are viable but more portal-dependent. BOA has a deterministic CGI
date query and PDF/object identifiers, but the canonical per-document ID needs a
specific rule. BON exposes stable issue and announcement routes plus announcement
codes, but no public XML/API/RSS surface was confirmed in this pass.

## Official Sources Consulted

| Source | Official URLs |
| --- | --- |
| DOGC | <https://dogc.gencat.cat/ca/>, <https://dogc.gencat.cat/ca/serveis/Consulta-del-DOGC/>, <https://dogc.gencat.cat/ca/serveis/Dades_obertes/index.html>, <https://dogc.gencat.cat/ca/serveis/verificar-documents/> |
| BOA | <https://www.boa.aragon.es/>, <https://www.boa.aragon.es/pdf/FolletoCarta2021-imp.pdf>, <https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VERLST&BASE=BOLE&DOCS=1-200&SEC=BUSQUEDA_FECHA&SEPARADOR=&PUBL=20260522> |
| BON | <https://bon.navarra.es/es>, <https://bon.navarra.es/es/busquedas>, <https://bon.navarra.es/es/indice-boletines>, <https://bon.navarra.es/es/que-es>, <https://bon.navarra.es/es/boletin/-/sumario/2026/99>, <https://bon.navarra.es/es/anuncio/-/texto/2026/99/1> |
| BOPV/EHAA | <https://www.euskadi.eus/bopv>, <https://opendata.euskadi.eus/api-bopv/?api=bopv>, <https://opendata.euskadi.eus/contenidos/recurso_tecnico/data_apirest/es_def/adjuntos/bopv.json>, <https://www.euskadi.eus/gobierno-vasco/atencion-ciudadania-servicios-digitales/-/noticia/2024/nueva-api-rest-del-boletin-oficial-del-pais-vasco-bopv/> |
| BOR | <https://web.larioja.org/bor-portada>, <https://web.larioja.org/bor-portada/bor>, <https://web.larioja.org/dato-abierto/datoabierto?n=opd-321>, <https://ias1.larioja.org/opendata/doc/administracion_publica/api_bor.pdf>, <https://web.larioja.org/bor-portada?fecha=2025-06-17> |

## Audit Table

| source_code | source_name | official_url | date-to-issue strategy | document list strategy | stable issue ID | stable document ID | HTML | XML | PDF | JSON/API/RSS | no-publication behavior | citation feasibility | raw hash feasibility | complexity | priority | biggest risks | MVP recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DOGC | Diari Oficial de la Generalitat de Catalunya | <https://dogc.gencat.cat/ca/> | Use official date/search flow and daily summary. Treat date to issue number as a discovery step; DOGC publishes Monday-Friday except Catalunya-wide or DOGC-seat holidays, with exceptional holiday publication possible. | Parse daily summary/portal response, then resolve document pages by `documentId` and CVE. | DOGC issue number plus date; summary CVE format `DOGC-N-XXXX-S`. | Official CVE format `CVE-DOGC-N-XXXXXXXX-XXXX`; portal `documentId` is useful but secondary. | yes, official and authentic for current period | yes, official page states XML Akoma Ntoso plus RDF/Turtle | yes | public open-data datasets for normative subset; no formal OpenAPI confirmed; portal page exposes internal `/eadop-rest/api/dogc/documentDOGC`; RSS not confirmed | no issue on non-publication date; exact portal response needs fixture | high | high, hash HTML/XML/PDF bytes; prefer XML/HTML for metadata MVP | medium | P2 | undocumented REST contract, bilingual/variant handling, date-to-summary endpoint discovery, legal-authenticity period differences | metadata-only MVP after endpoint discovery: date -> summary -> CVE/documentId -> HTML/XML/PDF URLs; hash raw HTML/XML; no PDF download by default |
| BOA | Boletin Oficial de Aragon | <https://www.boa.aragon.es/> | Use official CGI date query `CMD=VERLST...PUBL=YYYYMMDD`; sample `20260522` returned BOA number 96. Calendar/search exists on portal. | Date result lists issue sections, titles, `VERDOC` document links and `VEROBJ` PDF/signature objects. | issue number plus date, e.g. `BOA-2026-96`; page also exposes bulletin object ids such as `BBOLE2026052296`. | Best MVP key is `source/date/issue/DOCR` plus PDF `MLKOB`; some PDFs expose `csv: BOAYYYYMMDDNN`, but this needs fixture confirmation for all docs. | yes | not confirmed | yes | RSS service and Open Data BOA are advertised; no formal JSON/XML API confirmed in this pass | date query should return no issue or empty result on non-publication date; exact text not checked | medium-high | high for raw HTML/PDF/signature bytes | medium | P2 | legacy CGI, ISO-8859-1 encoding, document ID normalization, PDF/signature object churn, no confirmed XML/API | metadata-only MVP using CGI date list and `VERDOC`; store BOA issue number/date, DOCR, title, section, MLKOB PDF URL; do not rely on CSV until confirmed |
| BON | Boletin Oficial de Navarra | <https://bon.navarra.es/es> | Use official calendar/index and issue route `/es/boletin/-/sumario/{year}/{number}`; calendar JSON embedded current `boletinId` values such as `2026.99`. | Summary and latest pages list announcements; document route is `/es/anuncio/-/texto/{year}/{issue}/{ordinal}`. | `boletinId=YYYY.NN`, issue number/year/date. | Announcement route plus official `Codigo del anuncio`, e.g. `F2606324`; use both. | yes | not confirmed | yes, issue PDF download route exists | no public API/RSS confirmed; calendar uses undocumented Liferay resource endpoint | calendar/index absence for date; exact no-publication page text not confirmed | high | high for raw HTML/PDF bytes | medium | P2 | undocumented Liferay endpoints, bilingual ES/EU variants, issue PDF resource params, no XML/API | HTML-first metadata MVP: resolve issue from calendar/index, parse summary, store route ID and `Codigo del anuncio`, preserve ES/EU links, hash raw HTML |
| BOPV | Boletin Oficial del Pais Vasco / EHAA | <https://www.euskadi.eus/bopv> | Prefer official REST API for acts by year/month, then filter by publish date; use BOPV summary pages for issue number/date when needed. | Official OpenAPI exposes `/bopv/administrative-acts`, `/bopv/administrative-acts/{year}`, `/{year}/{month}`, and `/{year}/{month}/{num-order}`. | issue number plus date; summary page pattern observed as `sYY_NNNN.shtml`. | API identifier, e.g. `YYYY/MM/NNNNN`; document filename/order such as `2602173a`; API order number is stable. | yes, `.shtml` | not confirmed for per-document XML; ELI/RDF datasets exist for legislation | yes, PDF is official/authentic; EPUB/text also exposed | yes, official JSON OpenAPI; RSS not required/not confirmed | no API results or no summary page for date; exact no-publication text not checked | high | high for raw API JSON plus HTML/PDF bytes | low-medium | P1 | API pagination/filter semantics, language suffixes `a/e`, API vs issue-summary reconciliation | best first northern MVP: API metadata ingestion by month/date, store API ID, title, dates, downloadable URLs, issue fields where available; hash raw JSON |
| BOR | Boletin Oficial de La Rioja | <https://web.larioja.org/bor-portada> | Use official `?fecha=YYYY-MM-DD`; sample non-publication date returned "No hay ningun BOR publicado en esta fecha." Search/list page exposes latest issue entries. | `/bor-portada/bor` lists announcements with BOR number/date, HTML links and PDF servlet links; official open-data page documents XML API for any bulletin/announcement. | BOR number plus date, e.g. `BOR-2026-96`. | Announcement id such as `anu-577471`; PDF reference includes same numeric id, e.g. `40517102-1-PDF-577471-X`. | yes | yes, official API offers BOR XML | yes | official XML API; JSON/RSS not confirmed | explicit no-publication HTML message on date page | high | high for raw XML/HTML/PDF bytes | low | P1 | API doc is PDF and older than portal UI, announcement id normalization, PDF servlet references | strong MVP: use XML API for issue/announcement metadata, fall back to HTML list for fixtures, store `anu-*`, BOR number/date, PDF URL; no PDF download by default |

## Source Notes

### DOGC Catalunya

Official findings:

- The consultation page states that DOGC can be consulted in HTML and PDF, and that each document is also offered in RDF, Turtle and XML.
- The open-data page states that DOGC and Portal Juridic documents can be consulted and downloaded in XML Akoma Ntoso, RDF, Turtle, ELI metadata, HTML and PDF.
- The verification page documents CVE formats for documents and summaries and states that HTML is the authentic official format from 2013-02-27 onward.

Adapter implication:

```text
DOGC is data-rich, but not first unless the date summary and REST endpoints are pinned.
```

Use CVE as the citation-grade document identifier. Use `documentId` only as the portal key.

### BOA Aragon

Official findings:

- The homepage exposes calendar, advanced search, authenticity checking, RSS, and Open Data BOA navigation.
- A targeted date query for `2026-05-22` returned `Numero 96 de 22/05/2026`.
- The same page listed 41 document rows with `VERDOC` links and `VEROBJ` PDF/signature objects.
- A targeted document HTML request returned `Publicado el 22/05/2026 (Nº 96)` and PDF object links.
- A targeted PDF object HEAD returned `Content-Type: application/pdf`.

Adapter implication:

```text
BOA is viable through official HTML/CGI, but ID normalization is the hard part.
```

Do not assume `DOCR` alone is enough across re-rendered result pages. Store the date,
issue number, `DOCR`, title, section, emitter and PDF object id together.

### BON Navarra

Official findings:

- The search page states that bulletins are available from May 1996 and PDF from March 2001.
- The current portal exposes a stable issue summary route and announcement routes.
- A targeted announcement page for `2026/99/1` linked back to `BOLETIN Nº 99 - 22 de mayo de 2026`.
- The same page exposed `Codigo del anuncio: F2606324`.
- The page script embedded calendar data with `boletinId` values such as `2026.99`.

Adapter implication:

```text
BON is a reasonable HTML MVP, but not an API-first source.
```

Use announcement code plus route coordinates. Keep ES/EU alternate links; do not collapse
language variants without a source-specific rule.

### BOPV/EHAA Pais Vasco

Official findings:

- Open Data Euskadi announced an official REST API for BOPV in 2024.
- The OpenAPI descriptor is available as JSON and declares `https://api.euskadi.eus` as server.
- The API exposes administrative-act list and lookup endpoints by year, month and order number.
- The API schema includes identifiers such as `2024/07/03477`, publication dates, titles and downloadable links.
- Current document pages expose stable `.shtml` and PDF paths; search confirmed issue/date text such as `N.º 95, viernes 22 de mayo de 2026`.

Adapter implication:

```text
BOPV/EHAA is the cleanest API-led northern source.
```

Prefer raw API JSON for metadata and hash it before parsing. Add issue-summary reconciliation
only where needed for issue-level citation fields.

### BOR La Rioja

Official findings:

- The BOR portal states it is a universal, free public service.
- It publishes every day except Saturdays, Sundays and national/La Rioja-wide holidays, with exceptional publication possible.
- The date page explicitly returned `No hay ningun BOR publicado en esta fecha` for `2025-06-17`.
- The latest list page exposed BOR number/date, announcement HTML links, and PDF servlet links.
- The official open-data page documents an API that returns any bulletin and any announcement in XML over HTTP.

Adapter implication:

```text
BOR is a strong P1 because it has both explicit no-publication behavior and official XML.
```

Use XML API as canonical once endpoint examples are extracted from the official API PDF.
Use HTML list checks as smoke fixtures only.

## Recommended MVP Order

1. BOPV/EHAA metadata MVP.
2. BOR metadata MVP.
3. DOGC endpoint-discovery task, then metadata MVP.
4. BON HTML metadata MVP.
5. BOA HTML/CGI metadata MVP after ID-normalization fixture pass.

All MVPs should remain source-indexing only:

- fetch one explicit date or issue;
- parse official metadata and official artifact URLs;
- compute SHA-256 over raw metadata payloads;
- store no candidates;
- download no PDFs by default;
- run no backfills.

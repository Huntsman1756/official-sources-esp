# Autonomous Islands and Mediterranean Bulletin Source Audit - 2026-05-21

## Scope

This report audits six future `official-sources` candidates:

- BOIB Illes Balears
- BOC Canarias
- BOC Cantabria
- BORM Region de Murcia
- BOCCE Ceuta
- BOME Melilla

This was research only:

- no VPS was touched;
- no database was touched;
- no candidates were created;
- no adapters were implemented;
- no backfills were run;
- no downstream projects were touched;
- no bulk PDF downloads or crawling were run.

The local helper router was not used because this task required current external knowledge and official web verification.

BOJA, DOGV, and BOCM are already audited, implemented, or partially implemented in nearby project work. They are useful comparison points only: BOJA remains the clean API-first benchmark, BOCM is a strong XML/HTML/PDF benchmark, and DOGV shows that dynamic official portals can still be viable when backend endpoints are stable.

## Executive Summary

Recommended implementation order, if these sources are promoted later:

```text
P1  BOIB
P1  BOC Canarias
P2  BORM Region de Murcia
P2  BOC Cantabria
P3  BOME Melilla
P4  BOCCE Ceuta
```

BOIB is the best source in this batch. It exposes official issue pages, official PDF as the authentic version, and official HTML/XML alternate versions per document via ELI-style URLs. BOC Canarias is also strong: date/issue pages are clean, document identifiers are stable, HTML and PDF are available, and RSS exists, but XML was not confirmed. BORM is promising because its Angular site is backed by official `services/*` XML endpoints and deterministic PDF endpoints. BOC Cantabria exposes issue XML and PDFs, but uses older servlet/action URLs and internal blob IDs. BOME has very good CVE-like identifiers and article HTML/PDF, but no public XML/API/RSS was confirmed. BOCCE should be deferred because it is mostly Joomla/JDownloads listing plus issue PDFs, with weak per-document structure.

## Audit Matrix

| source_code | official URL | date-to-issue strategy | document list strategy | stable issue ID | stable document ID | HTML | XML | PDF | JSON/API/RSS | no-publication behavior | citation feasibility | raw hash feasibility | expected adapter complexity | priority | biggest risks | MVP recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOIB | <https://www.caib.es/eboibfront/index.do?lang=es> | Use official calendar/month page or issue number/year search. The latest issue link resolves to `/eboibfront/es/YYYY/<internalIssueId>/`. | Parse the official issue page sections; each entry exposes PDF, HTML, and XML links. | BOIB number plus date, plus portal internal issue id, for example `BOIB 056 / 2026-05-02` and `/2026/12269/`. | Prefer ELI URL path; also store edict number and first page. Example edict `4273`, ELI path `/eli/es-ib-01070159/pre/2026/05/02/(1)/dof/spa/`. | Yes, official alternate version. | Yes, official alternate version. | Yes, official and authentic version. | RSS yes: <https://www.caib.es/eboibfront/indexrss.do?lang=es>. No JSON API confirmed. | Date absent or unlinked in the calendar should be treated as no issue; do not infer from weekday alone because extraordinary issues exist. | High. Use source, BOIB number/date, edict number, ELI URL, page range. | High. Hash raw issue HTML, document XML, and official PDF bytes when fetched. | Low. | P1 | Calendar has internal ids; bilingual variants and ELI URL escaping need fixtures. | Metadata-only MVP from issue HTML/XML links. Prefer XML for document text/metadata and PDF only as official artifact reference. |
| BOC_CANARIAS | <https://www.gobiernodecanarias.org/boc/index.html> | Use latest/archive pages by year and issue number path `/boc/archivo/YYYY/NNN/` or `/boc/YYYY/NNN`. | Parse issue HTML; it lists sections, entries, page counts, size, HTML link, signature link, and PDF download. | `BOC-S-YYYY-NNN` for summary plus `YYYY/NNN` issue path, for example `BOC-S-2026-098`. | `BOC-A-YYYY-NNN-NNNN`, for example `BOC-A-2026-098-1684`. | Yes, but pages state HTML is not official and PDF must be downloaded for official version. | Not confirmed. | Yes, official PDF for issue summary and each document. | RSS yes: <https://www.gobiernodecanarias.org/boc/feeds/>. No JSON API confirmed. | Date absent from archive/latest list should be no issue; issue pages also expose previous/next through archive navigation. | High. Use source, issue number/date, `BOC-A-*`, title, and official PDF/HTML URLs. | High. Hash issue HTML and official PDF; hash HTML as non-official metadata evidence. | Low-medium. | P1 | HTML is explicitly non-official; XML unavailable; RSS is topical rather than canonical full history. | Metadata-only MVP from issue HTML. Store PDF URL as official artifact and HTML as parse aid. |
| BOC_CANTABRIA | <https://boc.cantabria.es/boces/> | Use official search/calendar forms: date, issue number/year/type, or CVE. Issue page uses internal `idBolOrd`. | Parse `verBoletin.do?idBolOrd=<id>` issue page; it exposes summary PDF, full issue PDF, XML issue link, and document links. | Internal issue blob id plus public code, for example `idBolOrd=42003`, `BOC-S-2025-42003`, `BOC-2025-42003`. | Public PDF code such as `BOC-2025-8005` plus internal `idAnuBlob`, for example `425074`. | Yes, issue HTML and announcement action pages. | Yes, issue XML via `verXmlAction.do?idBlob=<id>`. | Yes, summary, issue, and document PDFs via `verPdfAction.do` and announcement links. | RSS entry exists in official navigation/contact, exact feed endpoint not captured in this audit. No JSON API confirmed. | Use official date search result. If the search returns no issue for date/type, record no-publication. Do not infer from weekdays because extraordinary issues exist. | High. Use source, BOC date/number/type, `BOC-*` code, internal blob id, title, and URL. | High. Hash raw XML first, then issue/document PDF when fetched. | Medium. | P2 | Older ISO-8859-1 HTML, servlet actions, internal blob IDs, ordinary vs extraordinary issue types. | MVP should use XML issue as primary metadata when available, with HTML fallback and no broad historical crawl. |
| BORM | <https://www.borm.es/> | Use official Angular route `/#/home/sumario/DD-MM-YYYY` or direct service `services/boletin/fecha/DD-MM-YYYY/sumario`. Checked service returned `SumarioBoletinDTO`. | Parse official XML summary service; it includes issue metadata and `anunciosBoletin` entries. | Service id plus issue number/year/date, for example `id=110513`, `numero=116`, `ano=2026`, `fechaPublicacion=22-05-2026`. | Announcement service id plus public NPE-like number/year. Example `id=842998`, `numero=2316`, `ano=2026`; PDF footer uses `NPE: A-220526-2316`. | Portal is HTML/Angular; no direct document HTML endpoint confirmed. | Yes, official XML summary service. | Yes. Issue PDF: `/services/boletin/ano/YYYY/numero/N/pdf`; document PDF: `/services/anuncio/ano/YYYY/numero/N/pdf`. | XML service endpoints yes. RSS UI exists at `/#/home/rss`; exact feed URL not captured. No JSON response confirmed for current service. | The date service should be probed; a missing or empty service response should mean no publication for that date. Do not infer from calendar alone. | High. Use source, issue number/date, NPE, announcement number/year, and official PDF URL. | High. Hash XML summary as canonical metadata; hash PDFs only when fetched as scoped artifacts. | Low-medium. | P2 | Angular frontend, undocumented service contract, XML shape may differ from older JSON examples, no HTML document endpoint confirmed. | MVP should use the XML summary endpoint by date and deterministic PDF URLs. No browser automation needed for metadata. |
| BOCCE | <https://www.ceuta.es/ceuta/bocce> | Use BOCCE/JDownloads category pages by year/month; issue filenames encode number and date, for example `BOCCE_6619_22-05-2026`. | Parse category/listing pages and issue PDFs. No reliable per-document HTML/XML list was confirmed. | Filename issue token, for example `BOCCE_6619_22-05-2026`; JDownloads view/download ids are also stable enough to store. | Weak. Notice numbers and page numbers inside the PDF are usable; no per-document public URL was confirmed. | Listing HTML only; no per-document HTML confirmed. | Not confirmed. | Yes, issue PDFs through JDownloads `viewdownload`/`finish` URLs. | No public JSON/API/RSS confirmed. | Date absent from year/month category should be no issue, but the category structure is noisy and should be checked with a targeted date/filename lookup. | Medium. Issue-level citations are strong; document-level citations need issue number, notice number, title, and page. | Medium-high for issue PDF; weaker for document records unless PDF segmentation is implemented. | High. | P4 | Joomla/JDownloads ids, sparse metadata, no per-document URLs, PDF-only extraction, category pages include unrelated document types. | Defer. If implemented, start with issue-level metadata only and a very small fixture set. |
| BOME | <https://bomemelilla.es/> | Use official year/month listing on home page, advanced search, or direct issue path `/bome/BOME-B-YYYY-NNNN` and extraordinary `/bome/BOME-BX-YYYY-N`. | Parse issue HTML; it lists departments, article CVEs, summaries, article PDF links, and article web views. | CVE-style issue id, for example `BOME-B-2026-6381`; extraordinary `BOME-BX-YYYY-N`. | CVE-style article id, for example `BOME-A-2026-568`; extraordinary `BOME-AX-YYYY-N`. Page ids use `BOME-P-*`. | Yes, issue summary and article pages. | Not confirmed. | Yes, full issue, summary, article, and page PDFs. | No public JSON/API/RSS confirmed. Email subscription exists. | A date absent from the year/month listing or search results should be no issue. Ordinary issues are Tuesday/Friday according to the official FAQ, but extraordinary issues can appear. | High. Use source, `BOME-B*`, `BOME-A*`, title, issue date, page id, and URL. | High. Hash issue HTML and article HTML; PDF hashes are straightforward for official artifacts. | Medium. | P3 | No XML/API, historical content before 2018 redirects to older Melilla site, ordinary/extraordinary ID families. | Metadata-only MVP from issue HTML and article HTML/PDF links. Avoid pre-2018 archive until separate discovery. |

## Source Notes

### BOIB Illes Balears

Official sources checked:

- Main portal: <https://www.caib.es/eboibfront/index.do?lang=es>
- Example issue: <https://www.caib.es/eboibfront/es/2026/12269/?lang=es>
- RSS feed: <https://www.caib.es/eboibfront/indexrss.do?lang=es>
- Example ELI/PDF path: <https://www.caib.es/eboibfront/eli/es-ib-01070159/pre/2026/05/02/(1)/dof/spa/pdf>
- Example ELI/HTML path: <https://www.caib.es/eboibfront/eli/es-ib-01070159/pre/2026/05/02/(1)/dof/spa/html>
- Example ELI/XML path: <https://www.caib.es/eboibfront/eli/es-ib-01070159/pre/2026/05/02/(1)/dof/spa/xml>

Observed evidence:

- The portal exposes a monthly calendar, latest issue link, issue number/year search, and full search.
- The checked issue page listed `Num. 056 - 2 / Mayo / 2026`.
- Each entry had a PDF link labelled as the official and authentic content.
- The same entry exposed HTML and XML as alternate versions.
- RSS returned `application/rss+xml`.

Assessment:

```text
date_to_issue: calendar or issue number/year search
document_list: issue HTML sections
stable_issue_id: BOIB number + date + portal issue id
stable_document_id: ELI URL + edict number
adapter_complexity: low
priority: P1
```

MVP recommendation:

Use issue HTML to discover document rows and official ELI artifact links. Fetch XML as primary machine-readable document evidence. Store the PDF URL as the official authentic artifact and fetch the PDF only when a scoped raw artifact hash is needed.

### BOC Canarias

Official sources checked:

- Main portal: <https://www.gobiernodecanarias.org/boc/index.html>
- Example issue: <https://www.gobiernodecanarias.org/boc/archivo/2026/098/>
- RSS feeds page: <https://www.gobiernodecanarias.org/boc/feeds/>
- Example document HTML: <https://www.gobiernodecanarias.org/boc/2026/088/1515.html>
- Example document PDF: <https://sede.gobiernodecanarias.org/boc/boc-a-2026-088-1515.pdf>

Observed evidence:

- The main page listed the latest issue as `BOC No 98 - 22 de mayo de 2026`.
- The issue page exposed summary PDF `BOC-S-2026-098`.
- Document entries used stable identifiers such as `BOC-A-2026-098-1684`.
- Document entries exposed `Version HTML`, signature, and PDF download links.
- Example HTML document page states that the HTML version is not official and the official version is the PDF.
- The RSS page lists feeds by section, department, cabildo, and university.

Assessment:

```text
date_to_issue: archive/latest page by issue number/date
document_list: issue HTML
stable_issue_id: BOC-S-YYYY-NNN and YYYY/NNN path
stable_document_id: BOC-A-YYYY-NNN-NNNN
adapter_complexity: low-medium
priority: P1
```

MVP recommendation:

Use issue HTML as the canonical metadata list and store both document HTML and PDF URLs. Treat PDF as official artifact. Use RSS only for recent discovery or smoke checks, not as full historical source.

### BOC Cantabria

Official sources checked:

- Main/search portal: <https://boc.cantabria.es/boces/>
- Last issue route: <https://boc.cantabria.es/boces/boletines.do?boton=UltimoBOCPublicado>
- Search/calendar route: <https://boc.cantabria.es/boces/boletines.do?boton=MesSiguiente>
- Example issue: <https://boc.cantabria.es/boces/verBoletin.do?idBolOrd=42003>
- Site map: <https://boc.cantabria.es/boces/inicioMapaWeb.do>

Observed evidence:

- The search page supports date/type, number/type/year, and CVE searches.
- Example issue HTML exposed summary PDF `BOC-S-2025-42003`, issue PDF `BOC-2025-42003`, XML issue `verXmlAction.do?idBlob=42003`, and document links.
- A checked HTML response used `text/html;charset=ISO-8859-1`.
- Links included document action ids such as `verAnuncioAction.do?idAnuBlob=425074`.
- The site map includes search, bulletin download, authentication/verification, and contact/RSS entries.

Assessment:

```text
date_to_issue: official date/type search
document_list: issue XML when available, issue HTML fallback
stable_issue_id: idBolOrd + BOC-S/BOC public codes
stable_document_id: BOC-YYYY-NNNN PDF code + idAnuBlob
adapter_complexity: medium
priority: P2
```

MVP recommendation:

Prefer `verXmlAction.do?idBlob=<id>` as raw metadata evidence. Fall back to issue HTML only when XML is missing. Preserve internal ids because public document codes alone may not be enough for navigation.

### BORM Region de Murcia

Official sources checked:

- Main portal: <https://www.borm.es/>
- Example date summary service: <https://www.borm.es/services/boletin/fecha/22-05-2026/sumario>
- Example issue PDF pattern: <https://www.borm.es/services/boletin/ano/2026/numero/116/pdf>
- Example document PDF pattern: <https://www.borm.es/services/anuncio/ano/2026/numero/2316/pdf>
- RSS route checked as an Angular page: <https://www.borm.es/#/home/rss>

Observed evidence:

- The main site is Angular-backed and includes `scripts/sumario`, `scripts/anuncio`, `scripts/datosAbiertos`, and `scripts/rss` modules.
- The date summary service returned HTTP 200 with `application/xml;charset=UTF-8`.
- The XML root was `SumarioBoletinDTO`.
- The checked summary returned issue metadata such as `id=110513`, `numero=116`, `ano=2026`, and `fechaPublicacion=22-05-2026`.
- The summary contained `anunciosBoletin` entries with document ids and numbers.
- Issue and document PDF endpoints returned `application/pdf` on targeted HEAD checks.

Assessment:

```text
date_to_issue: services/boletin/fecha/DD-MM-YYYY/sumario
document_list: SumarioBoletinDTO XML
stable_issue_id: service id + issue number/year/date
stable_document_id: announcement id + number/year + NPE
adapter_complexity: low-medium
priority: P2
```

MVP recommendation:

Use the XML service as the metadata source. Avoid browser automation for the Angular app. Store deterministic PDF URLs for issue and document artifacts, but do not fetch PDFs except for targeted verification or artifact hashing.

### BOCCE Ceuta

Official sources checked:

- BOCCE page: <https://www.ceuta.es/ceuta/bocce>
- BOCCE document category: <https://www.ceuta.es/ceuta/component/jdownloads/viewcategory/6-bocce>
- 2026 category examples: <https://www.ceuta.es/ceuta/component/jdownloads/viewcategory/1970-2026?Itemid=0>
- Example document detail: <https://www.ceuta.es/ceuta/component/jdownloads/viewdownload/1976/23141?Itemid=>
- Example direct issue download path observed by search: <https://www.ceuta.es/ceuta/component/jdownloads/finish/1976-mayo/23125-bocce-6613-01-05-2026?Itemid=0>

Observed evidence:

- The BOCCE page lists years and latest documents.
- Latest document examples use filenames such as `BOCCE_6619_22-05-2026` and `BOCCE_Extra18_20-05-2026`.
- JDownloads detail pages expose file title and file size.
- Direct `finish` URLs serve issue PDFs and indexed PDF text was visible in search results.
- No official per-document HTML, XML, JSON API, or RSS endpoint was confirmed.

Assessment:

```text
date_to_issue: year/month category pages and filename matching
document_list: issue PDF only, unless a richer hidden endpoint is later found
stable_issue_id: BOCCE filename token + JDownloads id
stable_document_id: notice number + page inside PDF
adapter_complexity: high
priority: P4
```

MVP recommendation:

Defer. If unavoidable, start with issue-level ingestion only: issue date, issue number, PDF URL, raw PDF hash, and parsed summary text. Do not attempt document-level extraction without a separate PDF segmentation design.

### BOME Melilla

Official sources checked:

- Main portal: <https://bomemelilla.es/>
- Example issue: <https://bomemelilla.es/bome/BOME-B-2026-6381>
- Example issue PDF: <https://bomemelilla.es/bome/descargar/BOME-B-2026-6381.pdf>
- Example issue summary page: <https://bomemelilla.es/bome/BOME-B-2026-6381/sumario>
- Example article page: <https://bomemelilla.es/bome/BOME-B-2026-6381/articulo/568>
- Advanced search: <https://bomemelilla.es/buscador-avanzado>
- FAQ: <https://bomemelilla.es/preguntas-frecuentes>

Observed evidence:

- The portal listed `BOME No 6381 del viernes, 22 de mayo de 2026` as the latest issue.
- The issue page exposed full issue PDF, summary PDF, web summary, and per-article download/web links.
- Article ids are visible as CVEs such as `BOME-A-2026-568`.
- The FAQ documents CVE families:
  - ordinary issue: `BOME-B-YYYY-NNNN`;
  - ordinary summary: `BOME-S-YYYY-NNNN`;
  - ordinary article: `BOME-A-YYYY-NNN`;
  - ordinary page: `BOME-P-YYYY-NNN`;
  - extraordinary equivalents: `BOME-BX`, `BOME-SX`, `BOME-AX`, `BOME-PX`.
- The FAQ says ordinary issues are currently published Tuesday and Friday, with extraordinary issues for urgent need.
- The FAQ states the electronic edition is official and authentic.
- The portal has email subscription, but no RSS/API/XML endpoint was confirmed.

Assessment:

```text
date_to_issue: year/month listing, advanced search, or direct BOME-B/BOME-BX path
document_list: issue HTML
stable_issue_id: BOME-B/BOME-BX CVE
stable_document_id: BOME-A/BOME-AX CVE
adapter_complexity: medium
priority: P3
```

MVP recommendation:

Use issue HTML and article HTML as metadata evidence. Store official PDF links at issue, article, and page level. Keep pre-2018 archive support out of scope until a separate discovery task covers the older `melilla.es` archive.

## Validation Notes

Only targeted checks were performed. No broad crawling or bulk downloads were used. The strongest verified machine-readable surfaces are:

- BOIB document XML links;
- BOC Cantabria issue XML link;
- BORM date summary XML service;
- BOME issue/article HTML with CVE ids.

The sources that should not be first implementation candidates are BOCCE and, to a lesser extent, BOME. Both are valid official sources, but BOCCE in particular lacks a clean document-level public surface.

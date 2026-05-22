# Autonomous western/central official sources audit

Audit date: 2026-05-22.

Scope: safe, punctual web checks only. No VPS, DB, candidates, adapters, backfills, bulk PDF downloads, crawling, or downstream work. Findings below are candidate-readiness notes for future `official-sources` work, based on official public web pages and a few HTTP header/API checks.

## Executive summary

| Source | Priority | Expected adapter complexity | MVP recommendation |
| --- | --- | --- | --- |
| BOCYL Castilla y Leon | High | Low to medium | Use the official JCyL open-data API first, fall back to BOCYL web pages for validation. |
| DOE Extremadura | High | Medium | Build from date calendar plus per-document HTML/XML/PDF links. XML makes it a strong candidate. |
| DOG Galicia | Medium-high | Medium | Build from static dated DOG paths and RSS/sumario pages; use HTML/PDF, defer XML/API assumptions. |
| BOPA Asturias | Medium | Medium | Build from dated sumary pages and `Cod.` document IDs; expect Liferay/redirect handling. |
| DOCM Castilla-La Mancha | Medium-low | Medium to high | Start with PDF/NID/date checks only; postpone richer extraction until HTML/detail behavior is profiled. |

## BOPA Asturias

- Official URL: https://sede.asturias.es/bopa. The checked pages redirect to `https://miprincipado.asturias.es/` while preserving BOPA query parameters and PDF paths.
- Date-to-issue strategy: query the sumary portlet by date, for example `bopa-sumario?...p_r_p_summaryDate=16%2F06%2F2025...`. The page exposes an issue heading such as `Boletin No 114 del lunes 16 de junio de 2025`.
- Document list strategy: parse the sumary HTML by section headings and disposition entries. Each entry has a title, `[Cod. YYYY-NNNNN]`, `Texto de la disposicion`, and `PDF de la disposicion`.
- Stable issue ID: issue number plus date, e.g. `BOPA 114/2025 2025-06-16`. Keep the original date because issue numbers reset annually.
- Stable document ID: the BOPA code, e.g. `2025-02893`. The detail endpoint uses it as `p_r_p_dispositionReference` and `p_r_p_dispositionText`; the PDF path also embeds it.
- HTML availability: yes. Detail pages expose `bopa-disposiciones` text views, but some pages warn that images may be omitted and the PDF is the complete legally valid version.
- XML availability: no public XML endpoint found in the sampled official pages.
- PDF availability: yes. PDFs use stable dated paths such as `https://sede.asturias.es/bopa/2025/04/09/2025-02893.pdf`, redirecting to `miprincipado.asturias.es`, and return `application/pdf`.
- JSON/API/RSS availability: no BOPA-specific public JSON/API/RSS found in the sampled official pages. The site has generic portal RSS areas, but not a verified BOPA feed.
- No-publication behavior: infer from the date-navigation sumary pages. Treat absence of a `Boletin No` heading/document list for the requested date as no publication; do not infer from HTTP 200 alone because the portal shell can still render.
- Citation feasibility: good. Cite `BOPA No`, publication date, section, title, and `Cod.`. Use the signed PDF URL as the canonical raw artifact.
- Raw hash feasibility: high for PDFs; medium for HTML because the Liferay shell and redirects add volatile markup. Hash the final PDF bytes and, if needed, the extracted document text after isolating the content area.
- Expected adapter complexity: medium. Main risks are Liferay query parameters, redirects from `sede.asturias.es` to `miprincipado.asturias.es`, occasional omitted images in HTML, and no verified machine-readable feed.
- Priority: medium.
- Biggest risks: portal markup churn, multilingual/redirect variants (`/ast/`, `/es/`), and legal completeness depending on PDF when HTML omits non-text content.
- MVP recommendation: issue discovery by date sumary, document IDs from `[Cod.]`, store HTML text plus signed PDF, and hash PDFs. Skip XML/API support until an official endpoint is identified.

## DOG Galicia

- Official URL: https://www.xunta.gal/diario-oficial-galicia/portalPublicoBusqueda.do?lang=gl.
- Date-to-issue strategy: use the public search/home page for date lookup and the static publication path pattern `/dog/Publicados/YYYY/YYYYMMDD/`. Current checks showed `DOG Num. 94 Venres, 22 de maio de 2026` and a sumary PDF at `/dog/Publicados/2026/20260522/Indice94_gl.pdf`.
- Document list strategy: parse the DOG search/current issue page sections and/or the dated sumary PDF/HTML links. Per-document static HTML pages follow paths such as `/dog/Publicados/2026/20260422/AnuncioG0766-080426-0001_es.html`.
- Stable issue ID: DOG issue number plus date, e.g. `DOG 94/2026 2026-05-22`.
- Stable document ID: best official public identifier is the static `Anuncio...` slug plus the `CVE-DOG` printed in PDFs/sumaries. The slug varies by publisher/date sequence; the CVE-DOG is better for citation and verification when present.
- HTML availability: yes. Per-document pages expose full HTML and language alternatives (`Galego`, `Castellano`, `Portugues`) plus a PDF link.
- XML availability: no public per-document XML found in sampled official DOG pages. The mobile app page uses an `.xml` content URL as page metadata, not as a DOG article API.
- PDF availability: yes. Sumaries and document pages provide PDF downloads, e.g. `Indice94_gl.pdf` and per-document `Descargar PDF`.
- JSON/API/RSS availability: RSS yes. The official RSS page states subscriptions by full sumary, sections, ranks, themes, and groups. No official JSON/API was verified.
- No-publication behavior: use the calendar/date lookup and static path existence. If a date has no issue in the portal and no dated `/Publicados/YYYY/YYYYMMDD/` issue assets, classify as no publication.
- Citation feasibility: high. Cite `DOG Num.`, date, page, section, title, and `CVE-DOG` when available.
- Raw hash feasibility: high for static HTML and PDF artifacts. Hash the language-specific HTML/PDF actually ingested.
- Expected adapter complexity: medium. Static paths are favorable, but language variants, PDF-only sumary details, and lack of verified XML/API add mapping work.
- Priority: medium-high.
- Biggest risks: multilingual duplicates, different identifiers for HTML slug vs CVE-DOG, and possible documents with annexes/tables where PDF is more authoritative than HTML.
- MVP recommendation: date issue lookup, parse the static issue/document links, ingest Galician and/or Spanish HTML plus PDF, keep `CVE-DOG` when present, and use RSS only as a freshness aid rather than the source of record.

## DOE Extremadura

- Official URL: https://doe.juntaex.es/.
- Date-to-issue strategy: use the official calendar, where publication days are marked, e.g. `Ordinario`. The home page exposes latest official diaries and calendar selection by month/year.
- Document list strategy: for each issue, parse the issue/document list to per-document HTML pages under `otrosFormatos/html.php?anio=YYYY&doe=...&xml=...`. The sampled official snippets expose metadata fields: `DOE Numero`, `Tipo`, `Fecha Publicacion`, `Apartado`, `Organismo`, `Rango`, descriptors, page start/end, and `Otros formatos: PDF XML`.
- Stable issue ID: `DOE {number}/{year} {type}`, e.g. `DOE 15/2026 Ordinario`; the URL also carries an encoded issue value such as `150o`.
- Stable document ID: the `xml` query parameter and PDF filename are stable candidates. Example: `xml=2026080063` maps to PDF `https://doe.juntaex.es/pdfs/doe/2026/150o/26080063.pdf`.
- HTML availability: yes via `otrosFormatos/html.php`.
- XML availability: yes, exposed by the official page as `Otros formatos: PDF XML`. The exact XML href should be read from the page anchors rather than guessed, because guessed `xml.php` paths returned 404 in a punctual check.
- PDF availability: yes. The sampled PDF URL returned `application/pdf`, `Last-Modified`, `ETag`, `Content-Length`, and byte ranges.
- JSON/API/RSS availability: RSS yes. The official DOE service charter text states a daily RSS service and availability commitment before 09:00 on publication days. No JSON API was found.
- No-publication behavior: calendar days without `Ordinario`/issue markers should be treated as no publication. Do not probe adjacent days broadly.
- Citation feasibility: high. Cite `DOE Numero`, type, date, section/apartado, page range, title, and document XML/PDF ID.
- Raw hash feasibility: high for PDFs and likely high for XML once the anchor URL is read. HTML is also useful but includes portal chrome.
- Expected adapter complexity: medium. Strong metadata and XML availability help, but URL conventions (`150o`, `xml` ID, PDF basename truncation) need careful normalization.
- Priority: high.
- Biggest risks: exact XML link discovery, issue type suffixes (`o` for ordinary and possible extraordinary variants), and official/legal precedence of signed PDFs vs other formats.
- MVP recommendation: date calendar to issue, per-document HTML list, extract metadata, ingest PDF and XML links from anchors, and hash both PDF and XML.

## BOCYL Castilla y Leon

- Official URL: https://bocyl.jcyl.es/portada.do.
- Date-to-issue strategy: use `boletin.do?fechaBoletin=dd%2FMM%2Fyyyy` or the calendar links from the portada. The sampled issue was `Sumario BOCYL no 90/2026` for `14 de mayo de 2026`.
- Document list strategy: preferred source is the official JCyL open-data dataset `bocyl` through the Opendatasoft Explore API. A punctual call to `https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl/records?limit=1` returned JSON with `no_edicion`, `fecha_publicacion`, section fields, title, page range, and PDF/XML/HTML links. Web sumary pages are a good cross-check.
- Stable issue ID: `no_edicion`, e.g. `90/2026`, plus `fecha_publicacion`.
- Stable document ID: `BOCYL-D-DDMMYYYY-ISSUE-DOCSEQ`, e.g. `BOCYL-D-14052026-90-1`. The same ID appears in PDF, XML, and HTML links.
- HTML availability: yes. API records include `enlace_fichero_html`, and web sumaries list `.html y otros formatos`.
- XML availability: yes. API records include `enlace_fichero_xml`.
- PDF availability: yes. API records include `enlace_fichero_pdf`, and web sumaries list document PDFs with sizes.
- JSON/API/RSS availability: JSON API yes through JCyL Opendatasoft; RSS and Atom yes from the official BOCYL RSS page, which lists complete and section feeds.
- No-publication behavior: the calendar shows only linked/marked publication dates. API filtering by `fecha_publicacion` should return zero records for no-publication dates.
- Citation feasibility: high. Cite `BOCYL no_edicion`, date, section, page range, title, and `BOCYL-D...` document ID.
- Raw hash feasibility: high. Hash the official XML and PDF artifacts. JSON API records are excellent for discovery but should not be the only raw legal artifact.
- Expected adapter complexity: low to medium. The API lowers complexity; still validate old records and HTTP vs HTTPS link normalization.
- Priority: high.
- Biggest risks: API completeness/lag relative to same-day BOCYL, historical coverage differences, and `http://` artifact links in API results that should be normalized carefully.
- MVP recommendation: use the Opendatasoft API as primary discovery, store JSON metadata plus official XML/PDF/HTML artifact URLs, and use BOCYL web sumary/RSS for freshness checks.

## DOCM Castilla-La Mancha

- Official URL: https://docm.jccm.es/portaldocm/.
- Date-to-issue strategy: use the DOCM calendar, where publication dates are marked `Ord.`, plus advanced search fields for `Fecha de publicacion` and `Numero de DOCM`.
- Document list strategy: start from date/number search or calendar issue pages, then collect detail/PDF links. Advanced search exposes fields for text, range, NID, publication date, and `Numero de DOCM`.
- Stable issue ID: DOCM number and year, e.g. `NN/YYYY`, plus publication date. Calendar labels show ordinary issues as `Ord.`.
- Stable document ID: NID. The official verification page defines NID as a unique identifier for any dispositions, acts, and announcements published in DOCM, printed in each document and used to access the original electronic document.
- HTML availability: partial/likely, but not as strong as BOCYL/DOG. Search results and official detail endpoints use `detalleDocumento.do?idDisposicion=...`; a sampled direct detail URL returned HTTP 500, so HTML detail handling needs profiling before relying on it.
- XML availability: no public XML found in sampled official pages.
- PDF availability: yes. Official download endpoint `docm/descargarArchivo.do?ruta=YYYY/MM/DD/pdf/YYYY_NNNN.pdf&tipo=rutaDocm` returned `application/pdf`.
- JSON/API/RSS availability: no public JSON/API/RSS verified. DOCM has a free email alert service, but that is not a public feed/API.
- No-publication behavior: calendar dates without `Ord.` should be treated as no issue. For programmatic checks, advanced search by exact publication date/issue number should return no documents.
- Citation feasibility: medium-high. Cite DOCM number/date/page/title and NID. NID gives a strong unique document handle even if discovery is more brittle.
- Raw hash feasibility: high for PDFs; medium for HTML/detail pages due session and occasional server errors. Prefer PDF hashing in MVP.
- Expected adapter complexity: medium to high. PDF URL patterns and NID are useful, but discovery and detail endpoints may require form/session handling.
- Priority: medium-low until discovery is proven.
- Biggest risks: brittle detail endpoint behavior, limited public machine-readable formats, possible reliance on search forms, and lack of RSS/API.
- MVP recommendation: implement only date/issue discovery plus PDF/NID capture after a focused pilot. Defer HTML extraction beyond basic metadata until stable detail URLs are confirmed.

## Official sources consulted

- BOPA Asturias:
  - https://sede.asturias.es/bopa
  - https://sede.asturias.es/ast/bopa-sumario?p_p_id=pa_sede_bopa_web_portlet_SedeBopaSummaryWeb&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal&p_r_p_summaryDate=16%2F06%2F2025&p_r_p_summaryIsSearch=false
  - https://sede.asturias.es/es/bopa-disposiciones?_pa_sede_bopa_web_portlet_SedeBopaDispositionWeb_mvcRenderCommandName=%2Fdisposition%2Fdetail&p_p_id=pa_sede_bopa_web_portlet_SedeBopaDispositionWeb&p_p_lifecycle=0&p_r_p_dispositionDate=09%2F04%2F2025&p_r_p_dispositionReference=2025-02893&p_r_p_dispositionText=2025-02893
  - https://sede.asturias.es/bopa/2025/04/09/2025-02893.pdf
- DOG Galicia:
  - https://www.xunta.gal/diario-oficial-galicia/portalPublicoBusqueda.do?lang=gl
  - https://www.xunta.gal/diario-oficial-galicia/suscricionsRSS.do?lang=es
  - https://www.xunta.gal/diario-oficial-galicia/oficialidade.do?lang=es
  - https://www.xunta.gal/dog/Publicados/2026/20260522/Indice94_gl.pdf
  - https://www.xunta.gal/dog/Publicados/2026/20260422/AnuncioG0766-080426-0001_es.html
- DOE Extremadura:
  - https://doe.juntaex.es/
  - https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=150o&xml=2026080063
  - https://doe.juntaex.es/pdfs/doe/2026/150o/26080063.pdf
  - https://doe.juntaex.es/cartaservicios/folleto.pdf
- BOCYL Castilla y Leon:
  - https://bocyl.jcyl.es/portada.do
  - https://bocyl.jcyl.es/boletin.do?fechaBoletin=14%2F05%2F2026
  - https://bocyl.jcyl.es/indiceRss.do
  - https://jcyl.opendatasoft.com/explore/dataset/bocyl/api/?flg=es-es
  - https://jcyl.opendatasoft.com/api/explore/v2.1/catalog/datasets/bocyl/records?limit=1
- DOCM Castilla-La Mancha:
  - https://docm.jccm.es/portaldocm/
  - https://docm.jccm.es/portaldocm/busquedaAvanzada.do
  - https://docm.jccm.es/docm/verificarNID.do
  - https://docm.jccm.es/docm/validarSuscriptor.do
  - https://docm.jccm.es/docm/descargarArchivo.do?ruta=2024/12/18/pdf/2024_9911.pdf&tipo=rutaDocm

## Validation notes

- Punctual HTTP checks confirmed PDF availability for BOPA, DOE, and DOCM sample artifacts without downloading PDF bodies.
- Punctual HTTP/API checks confirmed JCyL Opendatasoft JSON availability and returned PDF/XML/HTML fields for BOCYL.
- Punctual HTTP checks confirmed DOG RSS page availability and DOCM NID verification page availability.
- DOE XML availability is documented by official HTML snippets as an offered format, but exact XML URL extraction should be implemented by parsing official anchors, not by guessing paths.

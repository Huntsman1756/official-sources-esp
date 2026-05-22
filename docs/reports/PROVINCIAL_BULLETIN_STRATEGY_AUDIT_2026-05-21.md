# Provincial Bulletin Strategy Audit

Date: 2026-05-21
Verification pass: 2026-05-22
Scope: strategy-only audit of provincial official bulletins, starting from the BOE "Otros diarios oficiales" registry.

## Constraints Applied

- No VPS access.
- No database access.
- No candidate creation.
- No BOP adapter implementation.
- No backfills.
- No downstream project changes.
- No bulk PDF download and no full BOP crawling.
- Sample-only deep check. The sample reviewed was Alicante, Valencia, Zaragoza, Barcelona, Madrid, Sevilla, A Coruna, Bizkaia, Malaga, and Murcia.

The local helper-router policy was not applied because this task required current external official-source verification and cross-source judgement.

## Executive Summary

The BOE registry is a good authoritative seed list for provincial bulletins, but it is not a uniform technical registry. It links directly to each publisher, and the linked systems vary widely: modern HTML portals, older Struts/JSF-style applications, PDF-first archives, RSS/open-data feeds, custom search forms, and portals with browser/security friction.

The viable strategy is not a single generic BOP adapter. A generic adapter can cover navigation primitives and guardrails, but extraction should be platform-specific after a metadata-first monitoring phase.

Recommended BOP approach:

1. Use the BOE list as the authoritative inventory seed.
2. Build metadata-only monitoring first for a small set of high-signal provinces.
3. Prioritize platform-specific adapters for BOPs with stable document IDs and HTML/RSS availability.
4. Use oposiciones-only filters as a later layer on top of metadata, not as the first ingestion strategy.
5. Defer PDF-only and unknown/manual portals until the metadata layer proves value.

## BOE Seed List

Official seed: BOE, "Otros diarios oficiales", section "Boletines provinciales": https://www.boe.es/legislacion/otros_diarios_oficiales.php

The BOE page currently lists provincial bulletin links including A Coruna, Alicante, Barcelona, Bizkaia, Malaga, Sevilla, Valencia, Zaragoza, and many other provincial BOPs. It does not list Madrid or Murcia under "Boletines provinciales"; those are covered by autonomous official diaries, BOCM and BORM respectively, in the autonomous section.

## Technical Families

This classification is intentionally conservative. Only the sample received a deep check; non-sample provinces are grouped primarily by official BOE URL pattern and should remain `unknown/manual` until checked individually.

| Family | Definition | Sample evidence | Adapter posture |
| --- | --- | --- | --- |
| HTML index + stable document IDs | Issue page exposes document rows, IDs, metadata, and usually PDF/HTML links. | A Coruna, Barcelona, Malaga | Best MVP candidates. Platform-specific adapters realistic after metadata-only monitor. |
| JS/SPA search app + stable registry/CVE | Search/listing rendered by a web app; IDs exist but actions and downloadable formats may be JS-driven. | Valencia, Bizkaia, Sevilla | Metadata monitor realistic; full adapter needs portal-specific work and timeout handling. |
| Legacy server app with form search | Older Struts/servlet style forms and generated PDF paths. | Zaragoza | Metadata/search adapter possible, but should be isolated from modern adapters. |
| Date form / WordPress-sede wrapper | Public page exposes forms and headings, but actual result rendering is limited in static fetch. | Alicante | Manual or browser-assisted validation before adapter commitment. |
| RSS/open-data feed available | Official RSS/open data exists for daily bulletin or categories. | Barcelona, Bizkaia; Murcia for autonomous BORM | Strong monitoring input. Treat RSS as metadata feed, not as canonical full text until verified. |
| PDF-first / PDF-only | Issue or document content is mainly available as PDF; HTML metadata may be thin. | Sevilla issue PDF, Zaragoza historical/edict PDFs | Metadata-only first; full-text extraction later and only for selected categories. |
| Autonomous diary, not provincial BOP | Madrid and Murcia are not in BOE provincial BOP list. | BOCM, BORM | Out of BOP adapter scope unless project scope expands. |
| Unknown/manual | Official link exists but no sample check performed. | Most non-sample BOE provinces | Do not implement. Add to inventory backlog. |

## BOE Provincial Inventory: Initial Grouping

| Initial group | Provinces from BOE provincial list |
| --- | --- |
| Deep-checked in this audit | A Coruna, Alicante, Barcelona, Bizkaia, Malaga, Sevilla, Valencia, Zaragoza |
| Not in BOE provincial list but user-requested sample | Madrid, Murcia |
| BOE-listed, not deep-checked; keep `unknown/manual` | Albacete, Almeria, Araba/Alava, Avila, Badajoz, Burgos, Caceres, Cadiz, Castellon, Ciudad Real, Cordoba, Cuenca, Gipuzkoa, Girona, Granada, Guadalajara, Huelva, Huesca, Jaen, Las Palmas, Leon, Lleida, Lugo, Ourense, Palencia, Pontevedra, Salamanca, Santa Cruz de Tenerife, Segovia, Soria, Tarragona, Teruel, Toledo, Valladolid, Zamora |

Do not infer shared implementation from a similar Diputacion hostname alone. Domains like `bop.*`, `sede.*`, and `dip*.*` are naming conventions, not reliable platform contracts.

## Sample Deep Check

### Alicante

- Official BOE target: https://sede.diputacionalicante.es/consultas-bop/
- Checked official pages:
  - Consultas BOP: https://sede.diputacionalicante.es/consultas.bop/
  - Consultas edictos: https://sede.diputacionalicante.es/consultas-edictos/
- Date search: yes, by bulletin date on Consultas BOP; edict search has publication date range.
- Issue listing: present as "Boletin", "Sumario", and "BOP Completo", but static fetch did not expose populated sample rows.
- Document listing: edict search form exists with date range, extract text, publicante, and organism type.
- Formats observed: public UI implies sumario and full BOP; PDF/HTML/XML/JSON not confirmed from static sample.
- Stable document ID: not confirmed.
- RSS: not observed for BOP itself. The site exposes RSS links for employment/aid pages, not necessarily BOP documents.
- Complexity: high.
- Risk: high. Result rendering may be JS/backend-form dependent; stable IDs are not obvious.
- MVP adapter realistic: not for first phase. Keep as manual/metadata-only until a browser-assisted sample confirms result links and IDs.

### Valencia

- Official BOE target: https://bop.dival.es/bop/drvisapi.dll
- Checked official page: https://bop.dival.es/bop/xhtml/portal.xhtml
- Date search: yes. The portal exposes "Des de" and "Fins a" fields.
- Issue listing: yes. Current page showed a dated issue, "Butlleti Num. 96" on 2026-05-22.
- Document listing: yes. Rows include section, publisher, title, publication date, bulletin number, and `Num. registre`, for example `2026/05892`.
- Formats observed: official download URLs exist for document PDFs and full bulletin PDFs, for example `https://bop.dival.es/bop/downloads?anuncioNumReg=2026%2F01473&lang=es` and `https://bop.dival.es/bop/downloads?boletinFecha=09%2F03%2F2026&lang=es`.
- HTML/XML/JSON: HTML listing observed. JSON/API not confirmed.
- Stable document ID: yes, `Num. registre` appears stable enough for metadata identity.
- RSS: not observed.
- Complexity: medium-high.
- Risk: medium-high. Portal warns about browser compatibility and may rely on JS actions.
- MVP adapter realistic: realistic as platform-specific metadata adapter; full-text adapter after download-link rules are tested on a few IDs.

### Zaragoza

- Official BOE target: https://bop.dpz.es/BOPZ/
- Checked official pages:
  - Search form: https://bop.dpz.es/BOPZ/portalBuscarEdictos.do
  - Official BOP entry point: https://bop.dpz.es/BOPZ/
- Date search: yes. Search form exposes `Fecha de publicacion Desde/Hasta`.
- Issue listing: yes via "Ultimos boletines".
- Document listing: yes via "Buscar edictos".
- Formats observed: PDF paths are generated through `UploadServlet`, for example `https://bop.dpz.es/BOPZ/UploadServlet?ruta=Boletines\2023\143\Edictos\bop_4744_2023.pdf`.
- HTML/XML/JSON: HTML search form observed. JSON/API not confirmed.
- Stable document ID: yes-ish. Registration number and generated PDF filename patterns exist, but should be normalized carefully.
- RSS: not observed.
- Complexity: medium-high.
- Risk: medium. Legacy form/session URLs and escaped Windows-style PDF paths increase fragility.
- MVP adapter realistic: realistic for metadata/search with isolated legacy adapter; not a generic adapter target.

### Barcelona

- Official BOE target: https://bop.diba.cat/
- Checked official pages:
  - Home: https://bop.diba.cat/
  - Today's bulletin: https://bop.diba.cat/butlleti-del-dia
  - Search: https://bop.diba.cat/cercador-butlletins
  - Open data/RSS: https://bop.diba.cat/dades-obertes
- Date search: yes. Home page exposes date search in `dd-mm-aaaa`; bulletin page also exposes date and keyword search.
- Issue listing: yes. Home lists recent days and "El butlleti d'avui".
- Document listing: yes. Today's bulletin showed result rows with advertiser, title, `Registre`, and publication date.
- Formats observed: HTML listing, open-data/RSS feeds, and document pages. PDF availability should be confirmed per document during adapter design.
- HTML/XML/JSON: HTML and RSS confirmed. JSON/API not confirmed.
- Stable document ID: yes. `Registre`, e.g. `202610094158`, appears stable.
- RSS: yes. The official open-data page exposes daily RSS feeds by category and full daily content.
- Complexity: low-medium.
- Risk: low-medium.
- MVP adapter realistic: yes. This is one of the best first pilots for metadata-only monitoring and later document-level adapter.

### Madrid

- BOE provincial-list status: not listed under "Boletines provinciales".
- Official diary checked: BOCM, https://www.bocm.es/
- Date search: yes, BOCM exposes date, bulletin number/year, CVE, advanced search, and free text search.
- Issue listing: yes; current issue number and date shown.
- Document listing: yes, via summary and advanced search.
- Formats observed: full bulletin PDF, summary PDF, summary XML.
- Stable document ID: yes, BOCM CVE pattern such as `BOCM-20220107-2`.
- RSS: official RSS link present.
- Complexity: low-medium.
- Risk: low for autonomous-diary use, but high if misclassified as provincial BOP.
- MVP adapter realistic: not as BOP. Only include if the project intentionally expands to autonomous diaries.

### Sevilla

- Official BOE target: https://www.dipusevilla.es/bop/
- Checked official pages:
  - Current BOP portal: https://bopsevilla.dipusevilla.es/
  - Search: https://bopsevilla.dipusevilla.es/publica/buscador-anuncios/
  - Sample issue: https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/buscador/BOP-22-05-2026/
- Date search: yes via "Consulta de boletines"; search page supports terms and filters.
- Issue listing: yes. Current page showed "BOP num. 97 del 22/05/2026".
- Document listing: partial in static sample; issue page had "Anuncios 29" but rendered "No hay resultados" in the fetched view. PDF sumario and full BOP are available.
- Formats observed: sumario PDF and full BOP PDF. New portal also uses CVE-style issue IDs, e.g. `BOP-SE-2026-097`.
- HTML/XML/JSON: HTML shell confirmed. JSON/API not confirmed.
- Stable document ID: yes for issue/CVE; document-level CVE likely, but not confirmed from HTML sample.
- RSS: not observed.
- Complexity: medium.
- Risk: medium. Search/listing may require client-side execution or filters; historical archives split before December 2022 and before 1999.
- MVP adapter realistic: metadata-only for issue PDFs and CVE lookup is realistic; document-level extraction should wait.

### A Coruna

- Official BOE target: https://bop.dacoruna.gal/bopportal/
- Checked official pages:
  - Home: https://bop.dacoruna.gal/bopportal/
  - Latest issue: https://bop.dacoruna.gal/bopportal/ultimoBoletin.do
  - Previous bulletins: https://bop.dacoruna.gal/bopportal/boletinesAntiguos.do
  - Text search: https://bop.dacoruna.gal/bopportal/accesoBusqueda.do
- Date search: yes. Previous bulletins page exposes year/calendar navigation and states electronic editions are available from 2009-06-22.
- Issue listing: yes. Latest issue page showed "Sumario del Boletin No 95 - viernes, 22 de mayo de 2026".
- Document listing: yes. Rows include publisher hierarchy, document title, numeric ID, PDF link, and HTML web version.
- Formats observed: PDF and HTML per document; summary PDF per issue.
- HTML/XML/JSON: HTML and PDF confirmed. XML/JSON not observed.
- Stable document ID: yes. Example IDs include `2026/3269`, `2026/3233`, etc.
- RSS: not observed.
- Complexity: low-medium.
- Risk: low-medium.
- MVP adapter realistic: yes. Good candidate for first platform-specific metadata and document adapter.

### Bizkaia

- Official BOE target: https://apps.bizkaia.eus/BT00/
- Checked official page: https://www.bizkaia.eus/es/bob
- Date search: yes. Filters include BOB number/year, BOB from/to, announcement number, disposition number/date, emitters, document type, summary, and subject.
- Issue listing: yes. Current page showed latest bulletin, issue number, CVE, PDF bulletin, summary PDF, and announcement count.
- Document listing: yes via search results and latest bulletin link, though static sample focused on filter UI and latest issue card.
- Formats observed: bulletin PDF, summary PDF, search HTML, RSS help link.
- HTML/XML/JSON: HTML/PDF confirmed. JSON/API not confirmed.
- Stable document ID: yes. CVE pattern observed, e.g. `BOB-2026a095`; also announcement number filters.
- RSS: yes. Official help link "Canal de noticias RSS" is present.
- Complexity: medium.
- Risk: medium. Modern site has cookies and dynamic filters; should not be treated as simple static HTML.
- MVP adapter realistic: yes for metadata/RSS monitoring; document adapter after result-page URL and per-document IDs are verified.

### Malaga

- Official BOE target: https://www.bopmalaga.es/
- Checked official page: https://www.bopmalaga.es/
- Date search: yes via calendar.
- Issue listing: yes. Page showed "Boletin del 24/4/2026" with bulletin PDF and supplement PDF.
- Document listing: yes. Rows include visible "Ver edicto NNN/YYYY" and "Descargar PDF" links.
- Formats observed: HTML index, issue PDF, supplement PDF, document PDF.
- HTML/XML/JSON: HTML/PDF confirmed. XML/JSON not observed.
- Stable document ID: yes. Edict IDs such as `620/2026`, `1588/2026`, etc.
- RSS: not observed.
- Complexity: low-medium.
- Risk: low-medium.
- MVP adapter realistic: yes. Good first-phase candidate.

### Murcia

- BOE provincial-list status: not listed under "Boletines provinciales".
- Official diary checked: BORM, https://www.borm.es/
- Date search: yes on the official BORM site, though the fetched home page did not render full UI text in this environment.
- Issue listing: yes on BORM site; official `services` URLs expose bulletin and announcement documents.
- Document listing: yes for BORM publications.
- Formats observed: official service URLs expose PDFs. The BORM service charter states electronic BORM publication, online database consultation, RSS, alerts, authentication, and 24/7 web service.
- Stable document ID: yes. Service URL pattern includes year and announcement number, e.g. `https://www.borm.es/services/anuncio/ano/2023/numero/7465/pdf`.
- RSS: yes, per official BORM service material.
- Complexity: medium.
- Risk: low-medium for BORM itself, but high if classified as BOP.
- MVP adapter realistic: not as BOP. Only include if autonomous diaries become in scope.

## MVP Strategy

### Phase 0: Inventory Only

Maintain a checked inventory from the BOE "Boletines provinciales" list:

- province
- BOE official URL
- resolved official URL
- current technical family
- verification date
- sample URL checked
- observed formats
- observed stable ID
- recommended posture

No documents, candidates, or downstream effects should be created in this phase.

### Phase 1: Metadata-Only Monitoring

Start with BOPs that expose stable IDs and HTML/RSS:

1. Barcelona
2. A Coruna
3. Malaga
4. Bizkaia
5. Valencia
6. Sevilla
7. Zaragoza

Store only issue-level and document-level metadata in a scratch/non-production design until product requirements are clear:

- issue date
- issue number
- document ID/CVE/register number
- title
- publisher/entity
- section/category
- URL to official detail
- URL to official PDF/HTML if present
- observed format flags
- source fetch timestamp

### Phase 2: Platform-Specific Adapters

Do not start with a universal BOP parser. Use a shared adapter interface but separate implementations:

- `bopb_diba`: Barcelona RSS/HTML.
- `bop_dacoruna`: A Coruna portal.
- `bop_malaga`: Malaga calendar/index.
- `bop_bizkaia`: Bizkaia RSS/search/CVE.
- `bop_valencia`: Valencia register-number portal.
- `bop_sevilla`: Sevilla CVE/PDF issue portal.
- `bop_zaragoza`: legacy BOPZ search/UploadServlet.

Shared logic can include HTTP guardrails, date normalization, ID normalization, PDF link classification, language tags, and polite sampling. Extraction rules should stay platform-specific.

### Phase 3: Oposiciones-Only Layer

Add `oposiciones-only` filters only after metadata monitoring is stable. Suggested first filters:

- sections/categories: `Empleo Publico`, `Personal`, `Oferta Publica de Empleo`, `Procesos Selectivos`, `Recursos Humanos`
- title keywords: `bases`, `convocatoria`, `lista provisional`, `lista definitiva`, `admitidos`, `excluidos`, `bolsa de empleo`, `nombramiento`
- entity filters: municipalities and diputaciones

Risk: BOPs use varied taxonomy and languages. Keyword-only filtering will miss Catalan/Galician/Basque/Valencian variants unless localized dictionaries are maintained.

### Phase 4: Full Text and PDFs

Full-text extraction and PDF parsing should be deferred until metadata quality is proven. PDF parsing is likely needed for Sevilla/Zaragoza and for old archives, but should be narrowly targeted by category/date and never run as a blanket backfill.

## Adapter Decision Matrix

| Province/sample | Recommendation |
| --- | --- |
| Barcelona | Platform-specific adapter; high priority metadata/RSS pilot. |
| A Coruna | Platform-specific adapter; high priority metadata/document pilot. |
| Malaga | Platform-specific adapter; high priority metadata pilot. |
| Bizkaia | Metadata/RSS first; platform-specific adapter after document URL verification. |
| Valencia | Platform-specific metadata adapter; download extraction later. |
| Sevilla | Metadata-only issue/CVE monitor first; document extraction deferred. |
| Zaragoza | Legacy platform-specific adapter only; do not mix with modern HTML adapters. |
| Alicante | Defer; manual/browser-assisted validation required before MVP adapter. |
| Madrid | Not BOP. Keep outside provincial adapter scope. |
| Murcia | Not BOP. Keep outside provincial adapter scope. |
| Non-sample BOE provinces | Unknown/manual. Inventory-only until sampled. |

## Main Risks

- BOE is authoritative for links, not for technical capabilities.
- Similar URLs do not imply shared platform behavior.
- Some portals render key results via JavaScript or server session state.
- Document IDs differ by province: CVE, register number, edict number, bulletin number, service URL number.
- RSS availability does not guarantee full text or complete metadata.
- PDF-first portals can hide document-level structure inside the PDF.
- Madrid and Murcia are autonomous diaries, not provincial BOPs in the BOE provincial list.
- A generic adapter would likely create false confidence and brittle extraction.

## Recommended Next Step

Create no adapters yet. Create a small design issue or internal spec for a metadata-only BOP monitor using Barcelona, A Coruna, and Malaga as first pilots, then Bizkaia/Valencia/Sevilla/Zaragoza as second wave. Keep Alicante and all non-sample provinces as `unknown/manual` until each receives a similar small-sample check.

## Official Sources Consulted

- BOE, "Otros diarios oficiales": https://www.boe.es/legislacion/otros_diarios_oficiales.php
- Alicante BOP consultation: https://sede.diputacionalicante.es/consultas.bop/
- Alicante edict consultation: https://sede.diputacionalicante.es/consultas-edictos/
- Valencia BOP portal: https://bop.dival.es/bop/xhtml/portal.xhtml
- Valencia BOP download examples: https://bop.dival.es/bop/downloads?anuncioNumReg=2026%2F01473&lang=es and https://bop.dival.es/bop/downloads?boletinFecha=09%2F03%2F2026&lang=es
- Zaragoza BOP portal: https://bop.dpz.es/BOPZ/
- Zaragoza edict search: https://bop.dpz.es/BOPZ/portalBuscarEdictos.do
- Zaragoza PDF pattern example: https://bop.dpz.es/BOPZ/UploadServlet?ruta=Boletines\2023\143\Edictos\bop_4744_2023.pdf
- Barcelona BOP: https://bop.diba.cat/
- Barcelona daily bulletin: https://bop.diba.cat/butlleti-del-dia
- Barcelona search: https://bop.diba.cat/cercador-butlletins
- Barcelona open data/RSS: https://bop.diba.cat/dades-obertes
- Madrid BOCM: https://www.bocm.es/
- Sevilla BOP portal: https://bopsevilla.dipusevilla.es/
- Sevilla search: https://bopsevilla.dipusevilla.es/publica/buscador-anuncios/
- Sevilla sample issue: https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/buscador/BOP-22-05-2026/
- A Coruna BOP: https://bop.dacoruna.gal/bopportal/
- A Coruna latest issue: https://bop.dacoruna.gal/bopportal/ultimoBoletin.do
- A Coruna previous bulletins: https://bop.dacoruna.gal/bopportal/boletinesAntiguos.do
- A Coruna text search: https://bop.dacoruna.gal/bopportal/accesoBusqueda.do
- Bizkaia BOB: https://www.bizkaia.eus/es/bob
- Malaga BOP: https://www.bopmalaga.es/
- Murcia BORM: https://www.borm.es/
- Murcia BORM service URL example: https://www.borm.es/services/anuncio/ano/2023/numero/7465/pdf
- Murcia BORM service charter example: https://www.borm.es/services/anuncio/ano/2010/numero/16752/pdf?id=411676

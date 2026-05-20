# Autonomous and Statutory Territory Bulletin Source Audit - 2026-05-20

## Executive summary

This audit reviewed the first autonomous/statutory territory bulletin candidates for future `official-sources` adapters. No adapter was implemented, no database was modified, no candidates were created, and no bulk downloads were run.

Recommended first adapter:

```text
TASK-AUTO-002 - BOJA adapter MVP
```

BOJA is the strongest first implementation candidate because it exposes an official OpenAPI endpoint with date search, stable result IDs, JSON metadata, public URLs, PDF path metadata, and hash-related fields. BOCM is also promising, but its strongest public entry points are RSS, issue HTML, summary XML, and deterministic PDF paths rather than a formal API. DOGV has strong official formats and CVE identifiers, but the portal behavior is more dynamic and needs a focused endpoint discovery task before implementation. Ceuta and Melilla should be deferred until after one autonomous adapter is proven.

Terminology used in this report:

```text
BOE = state official source
Autonomous/statutory territory bulletins = independent official sources
Provincial/local bulletins = future heterogeneous sources
EU/DOUE = separate future source family
TED/OJ S = separate future procurement adapter
```

Do not use `autonomous BOE`.

## Audit table

| source_code | source_name | jurisdiction | region_code | official_url | has_api | api_documentation_url | has_rss | rss_url | has_date_search | has_keyword_search | has_html | has_xml | has_pdf | stable_ids | document_url_pattern | summary_url_pattern | rate_limit_policy_public | robots_or_terms_notes | calendar_or_publication_notes | content_types | encoding/language_notes | adapter_complexity | risk_level | recommended_priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOJA | Boletin Oficial de la Junta de Andalucia | Andalucia | ES-AN | https://www.juntadeandalucia.es/boja | yes | https://datos.juntadeandalucia.es/api/v0/boja/openapi.json | not confirmed | not confirmed | yes | yes | yes | unknown | yes | API `id`, for example `disposition.YYYY.NN.N` | `/api/v0/boja/{bid}`, `publicUrl`, and `pathPdf` | API search or bulletin endpoints | not found in quick audit | use conservative request pacing until documented | official API includes calendar/bulletin/search endpoints | JSON API, HTML portal, PDF | Spanish; API JSON | low | low | P1 | Best first adapter candidate. Use API JSON as canonical metadata and hash exact raw JSON payloads. |
| BOCM | Boletin Oficial de la Comunidad de Madrid | Comunidad de Madrid | ES-MD | https://www.bocm.es | no formal API found | not found | yes | https://www.bocm.es/rss, https://www.bocm.es/boletines.rss, https://www.bocm.es/ultimo-boletin.xml, https://www.bocm.es/sumarios.rss | yes | yes | yes | yes, summary XML | yes | `BOCM-YYYYMMDD-N`, issue `bocm-YYYYMMDD-NNN` | `/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-N.PDF` | `/boletin/bocm-YYYYMMDD-NNN`, plus `/boletin/CM_Boletin_BOCM/YYYY/MM/DD/BOCM-YYYYMMDDNNN.xml` | not found in quick audit | use conservative request pacing; RSS is not a crawling license | daily issue pages by date/number; latest RSS feeds available | HTML, RSS/XML, summary XML, PDF | Spanish | low-medium | medium | P1/P2 | Strong second candidate. Needs parser fixtures for RSS and issue XML/HTML. |
| DOGV | Diari Oficial de la Generalitat Valenciana | Comunitat Valenciana | ES-VC | https://dogv.gva.es | no formal OpenAPI found | not found | not confirmed | not confirmed | yes | yes | yes | yes, according to official FAQ/OpenData note | yes | CVE format `DOGV-[C/V]-YYYY-NNNNN`; summary CVE `DOGV-[C/V]-NNNNN-S` | `/datos/YYYY/MM/DD/pdf/YYYY_NNNNN_es.pdf`; HTML/XML available through portal patterns but need endpoint confirmation | `/datos/YYYY/MM/DD/PortalCAS.html` and portal daily publication pages | not found in quick audit | Liferay portal and some direct paths can return 403 without correct route/context | published on weekdays except weekends and regional/national holidays, with extraordinary publication possible | HTML portal, PDF, XML per official FAQ | Spanish and Valencian; bilingual official publication | medium | medium | P2 | Good candidate after BOJA/BOCM. Needs endpoint discovery and user-agent/session behavior tests before implementation. |
| BOCCE | Boletin Oficial de la Ciudad de Ceuta | Ceuta | ES-CE | https://www.ceuta.es/ceuta/bocce | no | not found | not found | not found | partial, via website/category pages | partial | yes | not found | yes | partial | Joomla/JDownloads `viewdownload` IDs; issue/document IDs require normalization | JDownloads category/list pages | not found in quick audit | use conservative manual discovery; no bulk crawling | issue PDFs and category pages are available; publication calendar needs confirmation | HTML listing, PDF downloads | Spanish | high | high | defer | Defer. MVP would need a resilient PDF/listing parser and explicit fixture coverage. |
| BOME | Boletin Oficial de Melilla | Melilla | ES-ML | https://bomemelilla.es | partial, site calendar/search endpoints observed but not documented | not found | email subscription, RSS not confirmed | not confirmed | yes | yes | yes | not found | yes | `BOME-B-YYYY-NNNN`, `BOME-BX-YYYY-N`, `BOME-S-YYYY-NNNN`, `BOME-A-YYYY-NNN` | `/bome/BOME-B-YYYY-NNNN/articulo/NNN` and `/bome/descargar/BOME-A-YYYY-NNN.pdf` | `/bome/BOME-B-YYYY-NNNN`, `/bome/BOME-B-YYYY-NNNN/sumario` | not found in quick audit | site has undocumented JSON endpoints; treat as unstable until confirmed | ordinary issues are currently Tuesday/Friday; extraordinary issues may appear | HTML pages, PDF downloads | Spanish | medium-high | medium-high | P3 | Official naming confirmed as BOME. Better than Ceuta structurally, but API is undocumented. |

## Detailed notes: BOCM

Official source reviewed:

- Main site: https://www.bocm.es/
- RSS page: https://www.bocm.es/rss
- Example daily issue page: https://www.bocm.es/boletin/bocm-20260519-117

Answers:

| Question | Finding |
| --- | --- |
| Can we fetch a daily issue by date? | Yes, if the issue number is known or discoverable through RSS/search/calendar. Example path uses `bocm-YYYYMMDD-NNN`. |
| Can we list all documents in that issue? | Likely yes. Daily issue pages expose the issue table and links to order-level PDFs; RSS/XML endpoints expose current/latest issue material. |
| Are there stable document identifiers? | Yes. Observed identifiers use `BOCM-YYYYMMDD-N`. |
| Can we retrieve HTML/XML/PDF per document? | PDF is clear. Summary XML is clear. Individual HTML needs a focused check before implementation. |
| Can we build a stable citation? | Yes: source code, issue date/number, document identifier, title, and official URL. |
| Can we compute source_snapshot_hash from raw payload? | Yes, from raw RSS/XML/HTML/PDF bytes. |
| Is the structure suitable for `official-sources` storage? | Yes. Summary-level and document-level metadata can fit the BOE-style storage model with source-specific fields. |
| MVP adapter shape | Fetch latest/date issue metadata, parse summary XML or issue HTML, store document metadata and official URLs, hash raw payloads, no candidate extraction. |
| What would break easily? | RSS only covers recent items; issue number discovery by date needs a stable strategy; HTML templates may change. |
| Should it be first adapter candidate? | It is viable, but BOJA is technically cleaner because of the official OpenAPI. |

Manual checks performed:

- BOCM RSS page documents feeds for latest bulletins, current issue orders, and recent summaries.
- Example issue page exposed issue PDF, summary PDF, summary XML, and individual order PDF links.
- Lowercase `.xml` summary URL returned successfully; uppercase `.XML` did not.

Assessment:

```text
adapter_complexity=low-medium
risk_level=medium
recommended_priority=P1/P2
```

## Detailed notes: DOGV

Official source reviewed:

- Main site: https://dogv.gva.es/
- FAQ / OpenData note: https://dogv.gva.es/es/preguntas-frecuentes
- Verifier page: https://dogv.gva.es/es/verificador-de-documents
- Example PDF pattern: https://dogv.gva.es/datos/2025/05/20/pdf/2025_16581_es.pdf

Answers:

| Question | Finding |
| --- | --- |
| Can we fetch a daily issue by date? | Yes through portal/calendar/search flows; direct static daily pages exist for older examples, but endpoint behavior needs focused discovery. |
| Can we list all documents in that issue? | Yes through daily summary pages/search, but the most stable machine route was not fully confirmed in this quick audit. |
| Are there stable document identifiers? | Yes. DOGV uses CVE identifiers. The verifier page documents `DOGV-[C/V]-YYYY-NNNNN` for provisions and `DOGV-[C/V]-NNNNN-S` for summaries. |
| Can we retrieve HTML/XML/PDF per document? | Official FAQ states documents can be obtained in XML, HTML, and PDF. Direct PDF URLs were confirmed. Some guessed direct XML/HTML paths returned 403, so endpoint discovery is required. |
| Can we build a stable citation? | Yes, using DOGV source code, CVE/signature, publication date, title, and official URL. |
| Can we compute source_snapshot_hash from raw payload? | Yes once the stable raw endpoint is selected. |
| Is the structure suitable for `official-sources` storage? | Yes, but not as first implementation without endpoint hardening. |
| MVP adapter shape | Resolve daily issue by date, parse daily summary/search result, store CVE/signature, title, language, official PDF/HTML/XML URLs, hash raw payloads. |
| What would break easily? | Liferay portal routes, session/context requirements, bilingual variants, and direct XML/HTML path assumptions. |
| Should it be first adapter candidate? | No. It should follow BOJA or BOCM after a dedicated DOGV endpoint discovery task. |

Assessment:

```text
adapter_complexity=medium
risk_level=medium
recommended_priority=P2
```

## Detailed notes: BOJA

Official source reviewed:

- BOJA portal: https://www.juntadeandalucia.es/boja
- OpenAPI document: https://datos.juntadeandalucia.es/api/v0/boja/openapi.json
- Example daily issue page: https://www.juntadeandalucia.es/eboja/2026/30/

Key OpenAPI paths observed:

```text
/api/v0/boja/all
/api/v0/boja/count
/api/v0/boja/search
/api/v0/boja/{bid}
/api/v0/boja/get/calendar
/api/v0/boja/get/bulletin
/api/v0/boja/get/search_pagination
```

The `search_pagination` endpoint supports date filters such as `date_from` and `date_to`, and the result fields include stable IDs, issue number/date, title section, organisation, summary, and document fields such as `publicUrl`, `pathPdf`, and `hashPdf` in the OpenAPI schema/enums.

Answers:

| Question | Finding |
| --- | --- |
| Can we fetch a daily issue by date? | Yes, via official API date filters and bulletin endpoints. |
| Can we list all documents in that issue? | Yes, API results can be filtered by date and paginated; issue pages also exist. |
| Are there stable document identifiers? | Yes. Example API result ID: `disposition.2026.94.5`. |
| Can we retrieve HTML/XML/PDF per document? | PDF and public URL metadata are exposed. HTML portal is available. XML was not confirmed in this quick audit. |
| Can we build a stable citation? | Yes, using BOJA source code, API ID, issue number, date, title, organisation, and public URL. |
| Can we compute source_snapshot_hash from raw payload? | Yes, from exact raw API JSON bytes and later artifact bytes. |
| Is the structure suitable for `official-sources` storage? | Yes. It maps cleanly to source snapshots, official documents, ingestion runs, and artifact metadata. |
| MVP adapter shape | API-only metadata ingestion by date; store document metadata, public URL, PDF path/hash if present, citation, raw JSON hash; no candidate extraction. |
| What would break easily? | API enum/field changes, pagination edge cases, and date format differences between API and portal. |
| Should it be first adapter candidate? | Yes. |

Manual checks performed:

- Fetched OpenAPI JSON successfully.
- Queried `search_pagination` for one date with `size=1`; it returned HTTP 200 and JSON metadata.

Assessment:

```text
adapter_complexity=low
risk_level=low
recommended_priority=P1
```

## Detailed notes: Ceuta / BOCCE

Official source reviewed:

- BOCCE page: https://www.ceuta.es/ceuta/bocce

Answers:

| Question | Finding |
| --- | --- |
| Can we fetch a daily issue by date? | Partially. Year/category pages and latest issue links exist, but a stable date API was not found. |
| Can we list all documents in that issue? | Probably through website listings or PDFs, but no clean machine endpoint was confirmed. |
| Are there stable document identifiers? | Partial. JDownloads IDs and visible issue names exist, but citation-grade document IDs need normalization. |
| Can we retrieve HTML/XML/PDF per document? | PDF is clear. HTML listing exists. XML was not found. |
| Can we build a stable citation? | Possible, but citation fields need source-specific rules. |
| Can we compute source_snapshot_hash from raw payload? | Yes, from exact HTML/PDF bytes. |
| Is the structure suitable for `official-sources` storage? | Eventually, but it is not a good first adapter. |
| MVP adapter shape | Parse one category/year listing, store issue metadata and PDF links, hash raw listing and PDFs on demand. |
| What would break easily? | Joomla/JDownloads route changes, category structure, PDF-only details, and weak document metadata. |
| Should it be first adapter candidate? | No. |

Assessment:

```text
adapter_complexity=high
risk_level=high
recommended_priority=defer
```

## Detailed notes: Melilla / BOME

Official naming:

```text
BOME - Boletin Oficial de Melilla
```

Official sources reviewed:

- BOME site: https://bomemelilla.es/
- FAQ: https://bomemelilla.es/preguntas-frecuentes
- Example issue page: https://bomemelilla.es/bome/BOME-B-2026-6380

Answers:

| Question | Finding |
| --- | --- |
| Can we fetch a daily issue by date? | The homepage lists recent ordinary and extraordinary issues with stable issue identifiers. A calendar endpoint exists in page markup but is undocumented. |
| Can we list all documents in that issue? | Yes, issue HTML pages list article CVEs and article links. |
| Are there stable document identifiers? | Yes. The FAQ documents CVE patterns such as `BOME-B-YYYY-NNNN`, `BOME-S-YYYY-NNNN`, and `BOME-A-YYYY-NNN`. |
| Can we retrieve HTML/XML/PDF per document? | HTML issue/article pages and PDF downloads are available. XML was not found. |
| Can we build a stable citation? | Yes, using BOME issue/article CVE, date, title/summary, and official URL. |
| Can we compute source_snapshot_hash from raw payload? | Yes, from raw HTML/PDF bytes. |
| Is the structure suitable for `official-sources` storage? | Yes, but the undocumented API/calendar pieces increase risk. |
| MVP adapter shape | Parse recent/date issue pages, store issue/article CVEs, article URLs, PDF URLs, raw HTML hashes; no candidate extraction. |
| What would break easily? | Undocumented endpoints, frontend route changes, and PDF-only article details. |
| Should it be first adapter candidate? | No. It is better after BOJA/BOCM. |

Assessment:

```text
adapter_complexity=medium-high
risk_level=medium-high
recommended_priority=P3
```

## Lightweight inventory for remaining autonomous bulletins

This is not a deep audit. It is a future-source inventory to avoid conflating source families.

| jurisdiction | likely source_code | source family | initial priority | note |
| --- | --- | --- | --- | --- |
| Galicia | DOG | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Asturias | BOPA | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Cantabria | BOC | autonomous/statutory territory bulletin | future audit | Source code collides semantically with other `BOC` names; namespace carefully. |
| Pais Vasco | BOPV/EHAA | autonomous/statutory territory bulletin | future audit | Bilingual source and identifier policy required. |
| Navarra | BON | statutory territory bulletin | future audit | Foral/statutory modeling note required. |
| La Rioja | BOR | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Aragon | BOA | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Cataluna | DOGC | autonomous/statutory territory bulletin | future audit | Official HTML/PDF/XML/RDF availability appears promising; not audited in depth here. |
| Illes Balears | BOIB | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Castilla y Leon | BOCYL | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Castilla-La Mancha | DOCM | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Extremadura | DOE | autonomous/statutory territory bulletin | future audit | Needs dedicated source assessment. |
| Murcia | BORM | autonomous/statutory territory bulletin | future audit | Do not confuse with BOE BORME. |
| Canarias | BOC | autonomous/statutory territory bulletin | future audit | Source code collision with Cantabria; namespace carefully. |

## Recommendation for first adapter

Recommended:

```text
TASK-AUTO-002 - BOJA adapter MVP
```

Reasons:

- Official OpenAPI exists and was reachable.
- Date-filtered search works with JSON responses.
- Stable API IDs exist.
- Metadata is already structured enough for `official_documents`.
- Raw JSON can be hashed before parsing.
- MVP can avoid PDFs, candidate extraction, and downstream writes.

BOCM should be the second candidate if BOJA MVP succeeds, because it has strong RSS/XML/PDF infrastructure and high downstream value, but likely needs more custom parsing than BOJA.

## Risks and unknowns

- Public rate limits were not clearly published for any audited source. Use conservative pacing and retry policies.
- DOGV direct XML/HTML endpoint behavior needs a focused discovery task; guessed direct paths can fail even when official formats exist.
- BOCM issue number discovery by date must be deterministic before implementation.
- Ceuta and Melilla may require PDF-first or HTML-listing-first adapters and should not inherit BOE assumptions.
- Electronic signature validation is not implemented in `official-sources`; hashes are integrity signals, not signature validation.
- Bilingual sources need explicit language/citation policy.
- Stable source codes must avoid collisions, especially `BOC`.

## Proposed TASK-AUTO-002 scope

```text
TASK-AUTO-002 - BOJA adapter MVP
```

MVP scope:

- Fetch BOJA official API metadata for one date.
- Store source snapshots from raw API JSON bytes.
- Store official document metadata:
  - BOJA API ID;
  - issue number;
  - publication date;
  - section/title section;
  - organisation;
  - summary/title;
  - public URL;
  - PDF path/hash metadata if present.
- Build deterministic citations.
- Record ingestion run status.
- Validate DB after ingestion.
- No candidate extraction.
- No XML/HTML/PDF artifact downloads unless explicitly approved in a later task.
- No downstream integration.
- No publication or approval workflows.

Suggested initial command shape:

```text
official-sources ingest-boja-date --date YYYY-MM-DD --dry-run
official-sources ingest-boja-date --date YYYY-MM-DD --write
```

## What not to implement yet

- Do not implement BOCM, DOGV, BOCCE, or BOME adapters in TASK-AUTO-002.
- Do not implement all autonomous/statutory territory bulletins at once.
- Do not implement provincial/local bulletin adapters.
- Do not implement EU/DOUE or TED/OJ S.
- Do not add RAG or LLM classification.
- Do not create source candidates from BOJA in the first adapter MVP.
- Do not write downstream evidence to EduAyudas or la-ayuda.
- Do not download large PDFs by default.

## Validation

This task was documentation and source audit only.

No code was changed. No test run was required.

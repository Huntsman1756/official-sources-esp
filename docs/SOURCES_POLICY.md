# Sources Policy

## Canonical Source Hierarchy

Canonical source data must come from official publication systems:

1. Official API responses.
2. Official XML.
3. Official HTML.
4. Official PDF.
5. Official metadata.

Third-party mirrors or convenience APIs are not canonical.

## Official Publication Tiers

The architecture decision for official source families is `docs/decisions/ADR-001-official-publication-hierarchy.md`.

Implemented now:

- Tier 1: BOE daily publications.
- Tier 1: BOE controlled XML/HTML/PDF artifacts.
- Tier 1: BOE consolidated legislation.
- Tier 1: BOE consolidated index and block retrieval.

Not implemented:

- Tier 2: autonomous/statutory territory bulletins.
- Tier 3: provincial/local bulletins.
- Tier 4: EUR-Lex/DOUE.
- TED/OJ S procurement adapter.

Do not use `autonomous BOE`. BOE is the state-level source and not a generic synonym for official bulletins.

## BOE MVP Source

The MVP canonical source is the official BOE open-data API:

- API overview: <https://www.boe.es/datosabiertos/api/api.php>
- BOE summary endpoint: `/datosabiertos/api/boe/sumario/{fecha}`
- Technical summary documentation: <https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf>

The official BOE FAQ states that the summary API exposes document URLs for PDF, XML, and HTML. Those URLs should be stored when available.

## BOE Request Policy

The BOE documentation describes endpoint behavior but does not clearly publish operational quotas or request rate limits. The runtime therefore uses conservative defaults:

```text
OFFICIAL_SOURCES_BOE_REQUESTS_PER_SECOND=1
OFFICIAL_SOURCES_BOE_MAX_RETRIES=5
OFFICIAL_SOURCES_BOE_BACKOFF_BASE_SECONDS=1
OFFICIAL_SOURCES_BOE_BACKOFF_MAX_SECONDS=30
OFFICIAL_SOURCES_BOE_JITTER_SECONDS=0.25
```

429, 503, and transient 5xx responses are treated as retryable with finite retries, exponential backoff, small jitter, and `Retry-After` handling when the header is present. Retry and throttle outcomes are audited; failures are not silently swallowed.

The BOE summary endpoint documents `404` as requested information not existing. For daily
summary ingestion, `404` is not retried aggressively and is recorded as `no_publication`:
the source was reached, no summary exists for that date, `last_http_status=404` is
preserved, document counts remain zero, and artifact download is skipped. This is not a
system failure. Real network, server, parser, storage, and schema failures remain
`failed`.

The current implementation uses `httpx` with an internal retry/backoff wrapper. `retryhttp` was not adopted in TASK-003F because that package is not available in the offline validation environment; equivalent behavior is covered by mocked HTTP tests.

## BOE Consolidated Legislation Source

TASK-003 and TASK-003B use only official BOE OpenData consolidated legislation endpoints.

Official documentation reviewed:

- FAQ: <https://www.boe.es/datosabiertos/faq/consolidada.php>
- API overview: <https://www.boe.es/datosabiertos/api/api.php>
- Technical PDF: <https://www.boe.es/datosabiertos/documentos/APIconsolidada.pdf>

Implemented endpoints:

```text
GET /datosabiertos/api/legislacion-consolidada/id/{id}
GET /datosabiertos/api/legislacion-consolidada/id/{id}/texto/indice
GET /datosabiertos/api/legislacion-consolidada/id/{id}/texto/bloque/{id_bloque}
Accept: application/xml
```

The complete-law endpoint returns consolidated norm XML with metadata and consolidated text when available. The index endpoint returns the official list of text blocks for the latest consolidated version. The block endpoint returns one official consolidated text block with its versions.

Official endpoints reviewed but not implemented:

```text
GET /datosabiertos/api/legislacion-consolidada
GET /datosabiertos/api/legislacion-consolidada/id/{id}/metadatos
GET /datosabiertos/api/legislacion-consolidada/id/{id}/metadata-eli
GET /datosabiertos/api/legislacion-consolidada/id/{id}/analisis
GET /datosabiertos/api/legislacion-consolidada/id/{id}/texto
```

The official identifier is the BOE consolidated law identifier, for example `BOE-A-YYYY-NNNNN`. The raw XML response body is hashed before parsing. Stored fields include the official identifier, title, law type, department, publication date, consolidation status, official URL, version hash metadata, and deterministic text blocks.

Accepted content type for implemented consolidated retrieval is `application/xml`. The BOE documentation also states that the index endpoint can return JSON, but this repository currently implements XML only to keep parsing deterministic and fixture-covered.

Raw payload hashing policy:

- compute SHA-256 from exact raw response bytes before XML parsing;
- store the same hash as `raw_payload_hash` and `source_snapshot_hash` for consolidated endpoint snapshots;
- preserve `previous_hash` when a known endpoint snapshot changes;
- create a consolidated-law integrity event for changed consolidated payloads.

Limitations:

- Search is not implemented in TASK-003.
- Own legal version comparison is not implemented.
- TASK-003B block retrieval stores official text blocks; it does not decide whether a block is current, applicable, or sufficient for legal analysis.
- The consolidated text is informational and must not be treated as legal advice.
- Hashes are integrity signals, not cryptographic authenticity.

## BOE Artifact Download Policy

Downloads must be driven by official URLs already stored from BOE metadata:

- `url_xml`
- `url_html`
- `url_pdf`

The downloader accepts only HTTPS URLs on official BOE hosts. It rejects non-BOE hosts, unsupported schemes, local file paths, and URL values that are not stored document artifact fields.

MCP tools do not expose arbitrary download functionality.

## Third-Party Sources

Third-party APIs, mirrors, and MCP projects may be used as prototyping references only. They must not be used as canonical infrastructure.

## EUR-Lex Future Policy

| Access path | Status | Decision |
| --- | --- | --- |
| Official EUR-Lex CELLAR API | Canonical future source | Allowed in a future EU adapter |
| EUR-Lex portal scraping | Unstable / often blocked | Do not use as canonical source |
| anamtb/boe-mcp EUR-Lex tooling | Experimental reference | Interface inspiration only |

Rules:

- EUR-Lex is not part of MVP-001.
- Do not implement EUR-Lex scraping.
- Do not rely on portal scraping.
- Future EUR-Lex support must use official APIs such as CELLAR or another documented official route.
- Any future EUR-Lex adapter must have its own source policy, ingestion audit, integrity checks, citation rules, and tests.

## Autonomous Bulletin Future Policy

Each autonomous bulletin needs its own adapter assessment. RSS availability does not imply stable parsing. HTML and PDF formats vary by bulletin.

Ceuta and Melilla require explicit modeling notes and must not be forced into the same model as ordinary autonomous communities without that note.

## Citation Requirements

Citations must identify the source code, external official identifier, publication date, title, and best official URL.

## Integrity Requirements

Integrity must hash raw source bytes before parsing or normalization. Hashes do not prove cryptographic authenticity unless electronic signature validation is implemented and tested. MVP signature status defaults to `not_checked`.

For downloaded artifacts, both `sha256` and `source_snapshot_hash` are computed from the exact raw downloaded bytes. XML and HTML text extraction happens after hashing. PDF hash storage is not electronic signature validation.

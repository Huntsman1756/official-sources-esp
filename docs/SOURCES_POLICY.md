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

The BOE summary endpoint documents `404` as requested information not existing. BOE publishes
every day of the year except Sundays. National holidays, 24 December, and 31 December can
still have BOE publication and must not be treated as no-publication days by default.

For daily summary ingestion, `no_publication` applies to Sundays only unless empirical API
evidence for a specific non-Sunday date proves otherwise and the date is explicitly allowlisted
in code. A Sunday `404` or Sunday no-summary response is not retried aggressively and is
recorded as `no_publication`: the source was reached, no summary exists for that date,
`last_http_status` is preserved, document counts remain zero, and artifact download is
skipped. This is not a system failure.

A non-Sunday valid summary is `success`. A non-Sunday `404`, network error, server error,
parser error, storage error, or schema error is `failed` unless that exact non-Sunday date is
explicitly allowlisted from observed BOE behavior. The implementation must not infer
`no_publication` from a holiday calendar.

BORME publication rules are different and must not be reused for BOE daily summary ingestion.

The current implementation uses `httpx` with an internal retry/backoff wrapper. `retryhttp` was not adopted in TASK-003F because that package is not available in the offline validation environment; equivalent behavior is covered by mocked HTTP tests.

## Controlled Range Ingestion Policy

`ingest-boe-range` is metadata-only. It ingests daily BOE summaries for an inclusive date range
and never downloads XML, HTML, or PDF artifacts.

Safety limits:

- `--max-days` defaults to `90`;
- ranges longer than `--max-days` fail clearly;
- ranges above `365` days require `--force`;
- ranges above `365` days also require `--confirm-large-range`;
- `--skip-existing` skips dates already recorded as `success` or `no_publication`;
- `--continue-on-no-publication` continues through controlled no-publication dates;
- `--stop-on-error` stops on real failures.

The command reuses the conservative BOE request policy with one shared client-side limiter
across the range. `--sleep-seconds` configures the limiter period. This is equivalent to a
single-request-per-period token pace for the synchronous range runner; no uncontrolled
concurrency is used.

Do not run broad historical BOE backfills by default. Project-specific backfills must document
date count, estimated request count, artifact policy, backup plan, and post-run report.

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

Summaries are the metadata/index layer. XML and HTML are candidate evidence layers. PDF is a
final evidence/on-demand layer and must be requested explicitly.

Candidate evidence review should use scoped artifact downloads:

```bash
official-sources download-boe-artifacts --candidate-ids 1,2,3 --types xml,html
official-sources download-boe-artifacts --document-ids 10,11,12 --types xml,html
```

Scoped downloads are mutually exclusive with `--date` so operators do not accidentally download
artifacts for a full BOE day while reviewing a small candidate set. The default artifact types
are `xml,html`.

PDF policy:

- PDF is never downloaded by default.
- PDF requires explicit `--candidate-ids` or `--document-ids`.
- PDF must not be downloaded for all candidates automatically.
- PDF must not be downloaded for all documents in a date range automatically.
- PDF should normally be used only for likely relevant candidates, final evidence selection,
  official PDF validation, or direct human review requests.
- PDF downloads create normal `artifact_download_attempts` rows and normal integrity records.

```bash
official-sources download-boe-artifacts --candidate-ids 1,3,10 --types pdf
```

## Candidate Prefiltering Policy

`find-source-candidates` is the preferred generic command for candidate prefiltering across
supported official sources. It performs keyword matching on stored official document titles and
metadata only. It does not parse full document content, call BOE/BOJA live APIs, download
artifacts, use LLMs, classify legal meaning, approve anything, publish anything, or write to
downstream projects.

`find-boe-candidates` remains as a backwards-compatible legacy/BOE-default command. It is
source-aware and accepts `--source`, but new operational docs should prefer
`find-source-candidates`.

Safe preview modes are available:

```bash
official-sources find-source-candidates \
  --source BOE \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --keywords "beca,ayuda,subvencion,convocatoria" \
  --dry-run --limit 50
```

`--dry-run` and `--no-write` are equivalent: they report matches and sample rows without
creating `source_candidates`. Write mode is explicit: operators must pass `--write` to create
candidate rows. In dry-run mode, `--limit` controls the number of sample matches printed. In
write mode, `--limit` caps the number of candidates created. It does not change the date range
scanned.

Results will include false positives. All candidates default to
`review_status=human_review_required`.

Matching precision rules:

- searchable text is lowercased, accent-normalized, and whitespace-normalized;
- original titles and metadata are preserved in output and storage;
- short terms such as `bono`, `beca`, and `ayuda` use word-boundary matching;
- `bono` matches `bono alquiler` but not `carbono`;
- multi-word terms such as `bases reguladoras` and `familia numerosa` are matched as phrases;
- deterministic scores are explainable prefilter signals, not legal or product decisions;
- score reasons are printed so reviewers can see why a document matched.

Optional filters are available:

```bash
official-sources find-source-candidates \
  --source BOE \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --keywords "convocatoria de ayudas,bases reguladoras" \
  --include-sections "III,V-B" \
  --exclude-sections "V-A" \
  --include-departments "Educacion,Formacion Profesional" \
  --dry-run
```

Stored BOE section names can be verbose. The CLI accepts shorthand aliases for common BOE
summary sections such as `V-A` for public procurement notices and `V-B` for other official
notices.

The `la-ayuda` / `EduAyudas` profile is available:

```bash
official-sources find-source-candidates \
  --source BOE \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --profile la-ayuda \
  --dry-run \
  --limit 100
```

Small write-mode pilots should use an explicit cap:

```bash
official-sources find-source-candidates \
  --source BOE \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --profile la-ayuda \
  --write \
  --limit 25
```

The profile is intentionally conservative:

- it excludes Section `V-A` public procurement notices by default;
- it treats standalone `convocatoria` and standalone `transporte` as weak/generic signals;
- `transporte` requires co-occurrence with aid-related terms such as `ayuda`, `subvencion`,
  `beca`, or `estudiantes`;
- `convocatoria de ayudas` and `convocatoria de subvenciones` are stronger than
  standalone `convocatoria`.

Example keywords for `la-ayuda` / `EduAyudas` only:

```text
beca
becas
ayuda
ayudas
subvencion
subvenciones
convocatoria
convocatoria de ayudas
convocatoria de subvenciones
bases reguladoras
educacion
estudiantes
alquiler
bono
bono alquiler
bono social
familia numerosa
discapacidad
transporte
vivienda
```

These keywords are not authoritative classification.

The BOJA-specific `boja-ayudas` profile is separate from `la-ayuda`:

```bash
official-sources find-source-candidates \
  --source BOJA \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --profile boja-ayudas \
  --dry-run \
  --limit 100
```

`boja-ayudas` keeps broad terms such as `ayudas`, `subvenciones`, `bases reguladoras`,
`convocatoria`, `vivienda`, and `alquiler` visible for exclusion accounting, but only
allows a candidate through when stronger metadata signals are present. Examples include
student/scholarship terms, `alumnado`, disability support, school material/transport/meal
terms, or youth-rent context. The profile intentionally avoids broad BOJA department terms
such as `universidad`, `educacion`, `formacion profesional`, and `familias` as direct
candidate keywords because they over-match BOJA metadata.

TASK-AUTO-004B refined BOJA 30-day metadata dry-run results from:

```text
la-ayuda on BOJA: 217/1500 = 14.47%
boja-ayudas on BOJA: 36/1500 = 2.40%
```

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

The 2026-05-20 source audit recommends BOJA as the first autonomous/statutory territory adapter candidate because it exposes an official OpenAPI endpoint with date search and structured document metadata. BOCM is a strong follow-up candidate because it exposes official RSS/current-issue XML, issue pages, and stable PDF paths, but it needs more custom parsing.

Autonomous/statutory territory adapter MVPs must start as metadata/index ingestion only:

- no candidate extraction by default;
- no downstream writes;
- no automatic approvals;
- no publication decisions;
- no large PDF downloads by default;
- raw official payloads must be hashed before parsing;
- each source needs source-specific citation and integrity rules.

DOGV, BOCCE, and BOME need additional endpoint hardening before implementation.

## BOJA MVP Source

TASK-AUTO-002 implements a narrow BOJA metadata adapter using the official Andalusian open-data API:

- OpenAPI: <https://datos.juntadeandalucia.es/api/v0/boja/openapi.json>
- Search endpoint: `/api/v0/boja/get/search_pagination`

Implemented BOJA query parameters:

```text
order_by=date
mode=DESC
size=200
page=0..n
date_from=YYYY-MM-DD
date_to=YYYY-MM-DD
```

Accepted content type is JSON. The adapter treats the raw JSON API response as the canonical metadata payload and hashes the exact raw bytes before parsing. Paginated BOJA responses are combined in page order before hashing:

```text
sha256(page0_raw + "\n---BOJA-PAGE---\n" + page1_raw + ...)
```

Stored BOJA document identifiers use the stable API `id` prefixed with the source code, for example:

```text
BOJA:disposition.2026.94.5
```

BOJA metadata ingestion stores official document metadata and `raw_api_response` file records. It preserves `publicUrl` as the best official public URL and `pathPdf` as the official PDF URL when available. It does not download PDFs, extract text, create candidates, write downstream projects, approve, or publish anything.

BOJA scoped artifact download is supported only for explicit candidate or document IDs:

```bash
official-sources download-boe-artifacts \
  --source BOJA \
  --candidate-ids 77,78 \
  --types pdf
```

BOJA date-level artifact download is not allowed. BOJA XML/HTML artifact download is not
implemented. PDF downloads require a persisted official `url_pdf` derived from verified BOJA
metadata. If `url_pdf` is missing, the scoped operation records a skipped artifact attempt and
does not infer or invent a URL.

BOJA evidence URL enrichment is a separate scoped metadata operation. The search endpoint's default
`campos` selection omits PDF/public URL fields. For selected documents, the detail endpoint can be
queried by stable BOJA `id`:

```text
GET /api/v0/boja/{bid}
```

The enrichment command is:

```bash
official-sources enrich-boja-evidence-urls \
  --candidate-ids 77,78
```

It accepts only explicit candidate or document IDs, updates persisted BOJA evidence URL metadata,
rejects non-official PDF URLs, and does not download PDFs.

BOJA official detail responses may return PDF URLs on `https://juntadeandalucia.es`. The downloader
does not follow arbitrary redirects. The parser therefore normalizes accepted BOJA PDF URLs to the
canonical `https://www.juntadeandalucia.es/eboja/...pdf` form before persistence.

BOJA no-publication semantics are independent from BOE. A BOJA API response with an empty `results` array is recorded as `no_publication`; BOE Sunday rules must not be reused.

Observed BOJA empty-date behavior can also be:

```json
{"status":400,"message":"Bad request"}
```

For valid date queries, only this exact generic BOJA JSON 400 body is treated as `no_publication`. The ingestion run preserves `last_http_status=400` and a diagnostic message. Other HTTP 400 bodies, HTTP 404 responses, 5xx responses, network errors after retries, parser errors, and malformed payloads remain failures unless future source-specific evidence and tests justify a narrower exception.

BOJA pagination completeness is mandatory. The adapter uses `total_hits` from the official API as the completeness target and continues fetching pages until all expected documents are collected. Missing `total_hits`, hitting `OFFICIAL_SOURCES_BOJA_MAX_PAGES_PER_DATE` before completion, or collecting fewer unique documents than `total_hits` fails the ingestion with `pagination_complete=false`. Page 0 must not be treated as complete when pagination metadata is ambiguous.

BOJA pilot closure:

- The first BOJA pilot validated metadata ingestion, source-specific candidate dry-runs, limited
  candidate creation, scoped URL enrichment, scoped PDF download, PDF evidence review, and
  `candidate_evidence_reviews` decision storage.
- BOJA produced `4` accepted downstream pilot candidates from the first reviewed evidence set.
- No downstream import has been performed.
- BOJA evidence should not be imported into EduAyudas or another downstream project until the
  downstream onboarding contract and environment-safe import path are documented.

## Downstream Onboarding Policy

Downstream integrations must follow `docs/DOWNSTREAM_ONBOARDING.md`.

Required policy:

- official evidence import must write to staging first;
- candidate creation must default to `pending_review`;
- publication must be downstream-owned and separate from import;
- source identifiers, citation metadata, integrity metadata, and artifact availability must be
  preserved;
- projects without staging/review foundation must implement foundation before importing evidence.

## Citation Requirements

Citations must identify the source code, external official identifier, publication date, title, and best official URL.

## Integrity Requirements

Integrity must hash raw source bytes before parsing or normalization. Hashes do not prove cryptographic authenticity unless electronic signature validation is implemented and tested. MVP signature status defaults to `not_checked`.

For downloaded artifacts, both `sha256` and `source_snapshot_hash` are computed from the exact raw downloaded bytes. XML and HTML text extraction happens after hashing. PDF hash storage is not electronic signature validation.

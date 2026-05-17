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

## Candidate Prefiltering Policy

`find-boe-candidates` performs keyword matching on stored BOE document titles and metadata
only. It does not parse full document content, call BOE, download artifacts, use LLMs,
classify legal meaning, approve anything, publish anything, or write to downstream projects.

Safe preview modes are available:

```bash
official-sources find-boe-candidates \
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
official-sources find-boe-candidates \
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
official-sources find-boe-candidates \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --profile la-ayuda \
  --dry-run \
  --limit 100
```

Small write-mode pilots should use an explicit cap:

```bash
official-sources find-boe-candidates \
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

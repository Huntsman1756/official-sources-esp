# BOCM Source Audit - 2026-05-21

## Scope

This report audits BOCM as a possible second autonomous/statutory territory source after BOJA.

This was research only:

- no adapter was implemented;
- no database was modified;
- no candidates were created;
- no downstream repository was touched;
- no broad downloads were run;
- no publication or approval action was performed.

## Executive Summary

BOCM is viable as the next autonomous/statutory territory source candidate.

Recommended decision:

```text
implement metadata-only BOCM adapter MVP after a focused date/issue discovery design
```

BOCM is less clean than BOJA because there is no formal OpenAPI equivalent. It is still promising
because the official site exposes:

- issue pages;
- RSS feeds;
- issue summary XML;
- document HTML pages;
- document PDF;
- document XML;
- document JSON-LD;
- stable CVE-style identifiers.

## Official Sources Reviewed

| Purpose | Official URL |
|---|---|
| Main BOCM site | <https://www.bocm.es/> |
| RSS page | <https://www.bocm.es/rss> |
| Structure page | <https://www.bocm.es/estructura> |
| Search guidance | <https://www.bocm.es/como-hacer-una-consulta?language=es> |
| Authentication and verification | <https://www.bocm.es/autentificacion-verificacion> |
| Sample issue page | <https://www.bocm.es/boletin/bocm-20260520-118> |
| Sample document HTML | <https://www.bocm.es/bocm-20260520-37> |
| Sample document PDF | <https://www.bocm.es/boletin/CM_Orden_BOCM/2026/05/20/BOCM-20260520-37.PDF> |
| Sample document XML | <https://www.bocm.es/boletin/CM_Orden_BOCM/2026/05/20/BOCM-20260520-37.xml> |
| Sample document JSON-LD | <https://www.bocm.es/boletin/CM_Orden_BOCM/2026/05/20/BOCM-20260520-37.json> |
| Sample issue summary XML | <https://www.bocm.es/boletin/CM_Boletin_BOCM/2026/05/20/BOCM-20260520118.xml> |

## Lightweight Access Checks

The audit performed only lightweight official URL checks. No broad crawling or bulk download was
run.

Observed `HEAD` results:

| URL type | Example | Result |
|---|---|---|
| Main site | `/` | `200 text/html` |
| RSS page | `/rss` | `200 text/html` |
| Issue page | `/boletin/bocm-20260520-118` | `200 text/html` |
| Document HTML | `/bocm-20260520-37` | `200 text/html` |
| Document XML | `/boletin/CM_Orden_BOCM/2026/05/20/BOCM-20260520-37.xml` | `200 text/xml` |
| Document JSON-LD | `/boletin/CM_Orden_BOCM/2026/05/20/BOCM-20260520-37.json` | `200 application/ld+json` |
| Summary XML | `/boletin/CM_Boletin_BOCM/2026/05/20/BOCM-20260520118.xml` | `200 text/xml` |

RSS checks:

| Feed | Result |
|---|---|
| <https://www.bocm.es/boletines.rss> | `200 application/rss+xml` |
| <https://www.bocm.es/ultimo-boletin.xml> | `200 application/rss+xml` |
| <https://www.bocm.es/sumarios.rss> | `200 application/rss+xml` |

## Access By Date

BOCM has a date search form on the main site:

```text
POST /search-day-month
field_date[date]
```

It also has number/year search:

```text
POST /search-number-year
field_bocm_number
field_date_y_hidden[year]
```

Issue pages are stable once date and issue number are known:

```text
/boletin/bocm-YYYYMMDD-NNN
```

Open question for MVP:

```text
date -> issue number discovery
```

The adapter should not assume a date-only URL. A safe MVP should first implement deterministic
issue discovery from RSS/latest issue plus the official date/number forms, then fixture it.

## RSS

The official RSS page exposes three useful feeds:

```text
https://www.bocm.es/boletines.rss
https://www.bocm.es/ultimo-boletin.xml
https://www.bocm.es/sumarios.rss
```

Recommended use:

- use RSS for latest/recent issue discovery and smoke fixtures;
- do not treat RSS as a complete historical source;
- do not use RSS as a license for broad crawling;
- pair RSS with issue pages and summary XML for canonical metadata.

## HTML, XML, PDF, and JSON-LD

BOCM exposes a richer per-document surface than expected.

For a sample CVE:

```text
BOCM-20260520-37
```

Observed official artifact patterns:

```text
HTML:   https://www.bocm.es/bocm-YYYYMMDD-N
PDF:    https://www.bocm.es/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-N.PDF
XML:    https://www.bocm.es/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-N.xml
JSONLD: https://www.bocm.es/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-N.json
```

Issue summary XML pattern:

```text
https://www.bocm.es/boletin/CM_Boletin_BOCM/YYYY/MM/DD/BOCM-YYYYMMDDNNN.xml
```

For metadata ingestion, prefer:

1. summary XML;
2. document XML;
3. document JSON-LD;
4. document HTML;
5. PDF only as scoped evidence.

PDF should not be downloaded in a metadata MVP.

## Stable Identifiers and Citation

BOCM uses CVE-style document identifiers:

```text
BOCM-YYYYMMDD-N
```

The official verification page states that the CVE identifies uniquely the provisions, acts, and
notices published in BOCM and allows access to the original electronic document on `www.bocm.es`.

Citation fields can be built from:

- `source_code=BOCM`;
- official identifier/CVE;
- issue date;
- issue number;
- section/subsection;
- department/issuer;
- title;
- official URL;
- artifact URLs when present.

## Authenticity and Hashing

BOCM's authentication and verification page states that the electronic BOCM on `www.bocm.es` is
official and authentic and that electronic publication from 2010-02-12 includes advanced
electronic signature.

The page also explains that each published provision has its own signature and CVE.

For `official-sources` integrity:

- compute SHA-256 from exact raw bytes before parsing;
- store raw payload hash for summary XML and document XML/JSON/HTML;
- treat PDF signature validation as future work unless a dedicated signature-validation task is
implemented;
- store hashes as integrity signals, not legal interpretation.

## Adapter MVP Shape

Recommended first MVP:

```text
metadata/index-only BOCM adapter
```

Suggested steps:

1. Fetch latest issue RSS or a single explicit issue page.
2. Resolve issue date and issue number.
3. Fetch issue summary XML.
4. Parse document identifiers, titles, sections, issuers, and official URLs.
5. Store `official_documents` with `source_code=BOCM`.
6. Persist URL fields for HTML, XML, JSON-LD, and PDF where deterministically available.
7. Hash raw summary/document XML payloads.
8. Do not create candidates.
9. Do not download PDFs.
10. Do not write downstream.

Only after metadata MVP succeeds should candidate prefiltering be considered.

## Risks Compared With BOJA

| Area | BOJA | BOCM |
|---|---|---|
| Formal API | Official OpenAPI | No formal OpenAPI found |
| Date search | API date filters | Web forms plus issue URL patterns |
| Pagination | API `total_hits` guard | Issue/summary parsing needed |
| Evidence URLs | Detail endpoint enrichment | Deterministic artifact URL patterns and page links |
| Artifact types | PDF validated | HTML, XML, JSON-LD, PDF observed |
| Identifier | API `id` plus bulletin fields | CVE `BOCM-YYYYMMDD-N` |
| Adapter complexity | Low | Low-medium |
| Risk | Low | Medium |

Main BOCM risks:

- no formal API contract;
- date-to-issue-number discovery needs careful fixtures;
- Drupal/form behavior may change;
- RSS is recent-only and not a historical source;
- HTML pages include a warning that displayed text may not be exact/complete compared with signed PDF;
- PDF signature validation is not implemented.

## Candidate/Downstream Policy

Do not run candidate extraction in the BOCM MVP.

The first adapter task should be:

```text
metadata only
no candidates
no PDFs
no downstream
no publication
```

Recommended later candidate profile work should happen only after:

- metadata ingestion is fixture-covered;
- BOCM issue/date discovery is reliable;
- a small date window has been audited;
- false-positive behavior is measured.

## Recommendation

Recommendation:

```text
implement BOCM as the second autonomous source, but start with a metadata-only MVP
```

Suggested next task:

```text
TASK-AUTO-BOCM-002 - BOCM metadata adapter MVP
```

Acceptance criteria for that task:

- single issue/date fixture;
- summary XML parsing;
- document XML/JSON-LD URL persistence;
- stable CVE citation;
- raw hash computation;
- no candidate creation;
- no PDF downloads;
- no downstream writes.

If the team wants one more research task before implementation, make it:

```text
TASK-AUTO-BOCM-001B - BOCM date-to-issue discovery probe
```

That probe should focus only on `POST /search-day-month`, number/year search, and RSS-to-issue
resolution.

## Validation

Documentation validation:

```text
git diff --check: passed
```

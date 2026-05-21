# BOCM Date-To-Issue Discovery Probe - 2026-05-21

## Scope

This report documents a focused probe for resolving BOCM publication dates to issue URLs and issue
numbers.

This was research only:

- no BOCM adapter was implemented;
- no database was touched;
- no candidates were created;
- no PDFs were downloaded;
- no broad crawl was run;
- no downstream repository was touched;
- MCP exposure was not changed.

## Objective

Resolve the main risk identified in `TASK-AUTO-BOCM-001`:

```text
date -> BOCM issue number
```

Example target mapping:

```text
2026-05-20 -> https://www.bocm.es/boletin/bocm-20260520-118
```

## Tested Dates

| Date | Expected kind | Result |
|---|---|---|
| 2026-05-20 | publication day | Resolved to issue `118` |
| 2026-05-19 | publication day | Resolved to issue `117` |
| 2026-05-18 | publication day | Resolved to issue `116` |
| 2026-05-17 | likely non-publication day, Sunday | No issue resolved; official search page reported no results |

## Strategies Tested

### 1. RSS Discovery

Official URLs tested:

```text
https://www.bocm.es/boletines.rss
https://www.bocm.es/ultimo-boletin.xml
https://www.bocm.es/sumarios.rss
```

Results:

| Feed | Result | Notes |
|---|---|---|
| `boletines.rss` | `200 application/rss+xml` | Exposed recent issue links, including the target date window. |
| `ultimo-boletin.xml` | `200 application/rss+xml` | Useful for latest issue content, but did not directly resolve issue links with the simple issue-link parser. |
| `sumarios.rss` | `200 application/rss+xml` | Useful as a summary feed, but not the best date resolver by itself. |

Example issue links found in `boletines.rss`:

```text
/boletin/bocm-20260518-116
/boletin/bocm-20260519-117
/boletin/bocm-20260520-118
```

Reliability:

```text
medium for recent issues
```

Failure modes:

- RSS is recent-window oriented, not a complete historical archive.
- RSS should not be treated as permission for broad crawling.
- Feed shape differs by feed; not all feeds expose issue URLs in the same way.

Implementation complexity:

```text
low
```

Recommended use:

```text
recent-issue fallback and smoke fixtures, not primary historical date resolution
```

### 2. Calendar / Date Search Page

Official form discovered on the BOCM main page:

```text
POST /search-day-month
field_date[date]=DD/MM/YYYY
```

GET with the same parameter was also observed to resolve successfully:

```text
GET /search-day-month?field_date%5Bdate%5D=DD%2FMM%2FYYYY
```

Probe results:

| Input date | Official search URL shape | Resolved issue URL | Issue number | Reliability |
|---|---|---|---:|---|
| 2026-05-20 | `/search-day-month` with `20/05/2026` | `/boletin/bocm-20260520-118` | 118 | high |
| 2026-05-19 | `/search-day-month` with `19/05/2026` | `/boletin/bocm-20260519-117` | 117 | high |
| 2026-05-18 | `/search-day-month` with `18/05/2026` | `/boletin/bocm-20260518-116` | 116 | high |
| 2026-05-17 | `/search-day-month` with `17/05/2026` | no issue URL | none | high for no-result detection |

The no-publication date returned the search page and text equivalent to:

```text
No se han encontrado resultados
```

Reliability:

```text
high for MVP, with fixtures
```

Failure modes:

- The endpoint is a website form endpoint, not a documented API.
- Form internals could change.
- The implementation must validate that the resolved issue URL date equals the requested date.
- No-result text should be treated conservatively and fixture-tested.

Implementation complexity:

```text
low-medium
```

Recommended use:

```text
primary date -> issue discovery strategy
```

### 3. Number / Year Search Endpoint

Official form discovered:

```text
POST /search-number-year
field_bocm_number=<issue_number>
field_date_y_hidden[year]=<year>
```

Probe results:

| Input issue/year | Resolved issue URL |
|---|---|
| 118 / 2026 | `/boletin/bocm-20260520-118` |
| 117 / 2026 | `/boletin/bocm-20260519-117` |
| 116 / 2026 | `/boletin/bocm-20260518-116` |
| 115 / 2026 | `/boletin/bocm-20260516-115` |

This confirms that issue numbers are stable and searchable, but issue number alone is not a date
resolver unless a candidate number is already known.

Reliability:

```text
high when issue number is known
```

Failure modes:

- Requires knowing or guessing the issue number.
- Sequential issue-number inference is unsafe across non-publication days.
- Example: issue `115` belongs to `2026-05-16`, while `2026-05-17` has no issue.

Implementation complexity:

```text
low
```

Recommended use:

```text
verification/fallback when an issue number is already known
```

### 4. Predictable URL Pattern

Issue URL pattern:

```text
https://www.bocm.es/boletin/bocm-YYYYMMDD-NNN
```

Summary XML pattern:

```text
https://www.bocm.es/boletin/CM_Boletin_BOCM/YYYY/MM/DD/BOCM-YYYYMMDDNNN.xml
```

Probe results:

| Date | Guessed issue | Issue page | Summary XML |
|---|---:|---|---|
| 2026-05-20 | 118 | 200 | 200 |
| 2026-05-19 | 117 | 200 | 200 |
| 2026-05-18 | 116 | 200 | 200 |
| 2026-05-17 | 115 | 404 | 404 |

Reliability:

```text
high after issue number is known, unsafe as discovery
```

Failure modes:

- The issue number cannot be derived from date alone without publication-calendar knowledge.
- Non-publication days break naive sequential guesses.
- A 404 can mean the date has no issue, or that the guessed issue number is wrong.

Implementation complexity:

```text
low after discovery
```

Recommended use:

```text
artifact URL construction after official date search resolves issue number
```

### 5. HTML Issue Index Discovery

Official pages tested:

```text
https://www.bocm.es/listado-de-boletines
https://www.bocm.es/listado-de-sumarios
```

Results:

- `listado-de-sumarios` exposed recent issue links, including the target date window.
- `listado-de-boletines` exposed issue links, but the default page did not start at the same date
  window as the probe targets.

Reliability:

```text
medium
```

Failure modes:

- Pagination and default sorting need explicit handling.
- It is a page parser, not a formal API.
- It is less direct than `/search-day-month` for a specific date.

Implementation complexity:

```text
medium
```

Recommended use:

```text
manual audit support or fallback, not primary MVP resolver
```

### 6. JSON-LD / Document Links As Fallback

Document JSON-LD exists for known CVE/document URLs:

```text
https://www.bocm.es/boletin/CM_Orden_BOCM/YYYY/MM/DD/BOCM-YYYYMMDD-N.json
```

Observed JSON-LD includes `isPartOf` data pointing to the issue:

```text
https://www.bocm.es/boletin/bocm-YYYYMMDD-NNN
```

Reliability:

```text
high after a document is known
```

Failure modes:

- It cannot resolve `date -> issue` by itself.
- It requires a known document identifier/CVE.

Implementation complexity:

```text
low
```

Recommended use:

```text
consistency check after document parsing, not primary date discovery
```

## Recommended Strategy

Primary strategy:

```text
Use official `/search-day-month` with `field_date[date]=DD/MM/YYYY`.
Follow the resolved final URL or parse the returned issue link.
Validate that the resolved issue URL date equals the requested date.
```

Expected outcomes:

| Outcome | Handling |
---|---|
| Resolves `/boletin/bocm-YYYYMMDD-NNN` for requested date | store issue date and number |
| Returns no issue and official no-results text | record controlled `no_publication` |
| Resolves an issue for a different date | fail as unexpected |
| HTTP/network/parser error | fail, do not infer no-publication |

Fallback strategy:

```text
Use `boletines.rss` / `listado-de-sumarios` for recent issue discovery.
Use `/search-number-year` only when an issue number is already known.
Use JSON-LD `isPartOf` only after document-level metadata is known.
```

Do not use predictable issue number increments as canonical discovery.

## Can TASK-AUTO-BOCM-002 Start?

Yes, with a narrow metadata-only scope.

Recommended next task:

```text
TASK-AUTO-BOCM-002 - BOCM metadata adapter MVP
```

Minimum MVP scope:

```text
date -> issue via /search-day-month
issue -> summary XML
summary XML -> document list
document metadata
official issue URL
official document HTML/XML/JSON-LD URLs
citation fields
raw hash of issue/search/summary payloads
ingestion_run
no candidates
no PDFs
no downstream
```

Required fixtures:

| Fixture | Purpose |
|---|---|
| 2026-05-20 | publication day, issue 118 |
| 2026-05-19 | publication day, issue 117 |
| 2026-05-18 | publication day, issue 116 |
| 2026-05-17 | no-publication Sunday/no-results case |

## Remaining Risks

- BOCM does not expose a formal OpenAPI like BOJA.
- `/search-day-month` is a website endpoint and may change.
- No-publication handling must be based on observed official no-results response, not calendar
  inference alone.
- Summary XML parsing must be fixture-covered before any metadata backfill.
- PDF download and signature validation remain out of scope for MVP.

## Validation

Documentation validation:

```text
git diff --check: passed
```

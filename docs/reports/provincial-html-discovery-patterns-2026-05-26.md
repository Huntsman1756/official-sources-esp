# Provincial HTML discovery patterns - 2026-05-26

Task: `TASK-SOURCE-PROVINCIAL-PATTERN-REPORT-001`

## Scope

This is an analysis/control-plane report. It compares the implemented provincial HTML discovery
monitors and decides whether the project has enough evidence for a reusable provincial HTML
framework.

Sources compared:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
```

Rejected/deferred example:

```text
BOP_ALMERIA
```

This task does not change parser behavior, add sources, write JSONL, create candidates, create
evidence-grade records, download PDFs/artifacts, run backfills, touch downstream repositories, run
VPS/prod DB operations, or add LLM classification.

## Current Implementation Shape

The current HTML monitor already has a small shared core:

- one-source dispatch through the registry access method;
- one URL builder per supported source;
- one parser per supported source;
- shared `HTMLParseResult`;
- shared output path construction;
- shared raw payload hashing;
- shared entry hashing;
- shared record builder;
- shared safety flags.

The extraction layer remains source-specific.

## Per-Source Parser Summary

### BOP_A_CORUNA

Registry access method:

```text
https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}
```

Date handling:

- input CLI/MCP date is `YYYY-MM-DD`;
- URL builder converts it to `DD/MM/YYYY`;
- the date is URL-encoded as `{date_ddmmyyyy}`;
- the requested date is used as `published_at`.

Parser strategy:

- fetches a date-scoped HTML summary page;
- parses `div.bloqueAnuncio` blocks with `HTMLParser`;
- tracks block depth and links inside each announcement block;
- extracts the entry id from the block `id`;
- extracts document id from text matching `YYYY/number`;
- extracts title from the first non-empty non-document-id link text that is not a PDF/HTML label;
- constructs `official_url` from the first `.html` link.

Hashing:

- `raw_page_hash` is SHA-256 of the raw HTML payload;
- `entry_hash` prefers `SHA256(source_code + published_at + official_url)`;
- fallback is `SHA256(source_code + document_id + title)` when `official_url` is missing.

PDF avoidance:

- the parser prefers HTML document URLs;
- PDF labels are ignored for title extraction;
- no PDF or artifact is downloaded.

Known limitations:

- relies on `bloqueAnuncio` block structure;
- assumes an HTML document URL exists for the announcement;
- source-specific block traversal is required.

### BOP_ALBACETE

Registry access method:

```text
https://bop.dipualba.es
```

Date handling:

- input CLI/MCP date is validated as `YYYY-MM-DD`;
- the current implementation fetches the current-bulletin page;
- the parser extracts the publication date from the bulletin header when present;
- if the page date cannot be extracted, it falls back to the requested date.

Parser strategy:

- fetches the official current-bulletin HTML page;
- extracts the bulletin date from text like `Boletin Numero N (DD/MM/YYYY)`;
- finds announcement title/link pairs with a source-specific regex over the HTML summary;
- extracts `document_id` and `entry_id` from the trailing number in the official page link;
- constructs `official_url` with `urljoin(page_url, href)`.

Hashing:

- `raw_page_hash` is SHA-256 of the raw HTML payload;
- `entry_hash` uses the shared preferred strategy based on `source_code + published_at + official_url`.

PDF avoidance:

- the `official_url` points to an official page/PDF endpoint;
- the monitor records the URL as metadata only;
- the record carries `pdf_endpoint_not_downloaded`;
- no PDF or artifact is downloaded.

Known limitations:

- current-bulletin page is not a date-bounded historical endpoint;
- date-scoped semantics are weaker than A Coruna or Alicante;
- parser depends on Bootstrap-like `col-12` and `text-end` layout;
- it is appropriate for preview/current-bulletin discovery, not backfill.

### BOP_ALICANTE

Registry access method:

```text
https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php
```

Date handling:

- input CLI/MCP date is `YYYY-MM-DD`;
- URL builder converts it to `DD/MM/YYYY`;
- the request uses the same `BOP_CON` XML parameter shape used by the official consultation page;
- parser converts `fechaPublica` from `DD/MM/YYYY` back to ISO date.

Parser strategy:

- fetches the official consultation-page backing endpoint one date at a time;
- response is JSON even though it belongs to the HTML consultation surface;
- extracts records from `boletin.bop[0].registro`;
- `document_id` comes from `edicto`;
- `entry_id` is `nBop-document_id`;
- title comes from `extracto`;
- `official_url` comes from `ubicacion`;
- summary combines `gndenom` and `ampliacion`.

Hashing:

- `raw_page_hash` is SHA-256 of the raw JSON payload;
- `entry_hash` uses the shared preferred strategy based on `source_code + published_at + official_url`.

PDF avoidance:

- `ubicacion` may be a PDF URL;
- the monitor records it as metadata only;
- the record carries `pdf_endpoint_not_downloaded`;
- no PDF or artifact is downloaded.

Known limitations:

- endpoint is a backing service for the HTML page, not a formal public API contract;
- fields are JSON lists, so parser logic is source-specific;
- empty days return a safe empty result or error payload rather than records;
- encoding/language content can be Spanish, Valencian, or mixed.

## Common Pattern

The three sources share the execution contract:

- one explicit source per command;
- one declared access method from `config/sources.yaml`;
- preview by default;
- JSONL writes only with explicit `--write`;
- raw payload fetched once per preview;
- SHA-256 `raw_page_hash`;
- deterministic `entry_hash`;
- output record shape:

```text
source_code
page_url
page_format
entry_id
document_id
title
published_at
official_url
summary
raw_page_hash
entry_hash
discovered_at
monitor_run_id
classification_status
evidence_status
candidate_status
warnings
```

Safety fields are shared:

```text
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

PDF/artifact behavior is also shared:

- links may be recorded as `official_url`;
- linked PDFs are not fetched;
- no artifact downloader is used;
- no candidate/evidence code path is called.

## Source-Specific Differences

| Area | BOP_A_CORUNA | BOP_ALBACETE | BOP_ALICANTE |
| --- | --- | --- | --- |
| Listing access | Date-scoped HTML page | Current-bulletin HTML page | HTML-page backing JSON endpoint |
| Date request | `DD/MM/YYYY` in URL | Requested date validated, page date extracted from current bulletin | `DD/MM/YYYY` in XML parameter |
| Parser style | `HTMLParser` block traversal | Regex over HTML summary layout | JSON field extraction |
| Document id | `YYYY/number` in link text | trailing numeric page id from URL | `edicto` |
| Entry id | HTML block `id` | same as page id | `nBop-document_id` |
| Title | first meaningful link text | title div before page link | `extracto` |
| Official URL | `.html` announcement URL | page/PDF endpoint URL metadata only | `ubicacion` URL metadata only |
| PDF handling | prefer HTML links | PDF/page endpoint recorded, not downloaded | PDF URL recorded, not downloaded |
| Empty-day behavior | depends on returned HTML page | current page may not match requested date | error payload or empty records |
| Reuse risk | class/block-name dependent | layout/regex dependent | backing-service schema dependent |

Important difference: only `BOP_A_CORUNA` and `BOP_ALICANTE` are naturally date-bounded. Albacete
currently proves current-bulletin observation, not a historical date lookup.

## Generalization Decision

Decision:

```text
Keep source-specific parsers for now.
Extract small shared helper functions only when duplication is already proven.
Do not build a generic provincial HTML framework yet.
```

Reasoning:

- the shared record contract is stable and already factored;
- hashing, output path, status flags, and URL dispatch are already shared enough;
- the actual extraction mechanics differ substantially across the three sources;
- one source is pure HTML block traversal, one is regex over current-bulletin HTML, and one is JSON
  returned by an official HTML-page backing endpoint;
- a generic parser would likely hide source-specific assumptions and increase false positives.

What can be shared safely:

- date parsing helpers;
- text normalization;
- URL joining;
- record construction;
- hash construction;
- refusal/error conventions;
- test assertions for metadata-only safety.

What should remain source-specific:

- selectors;
- endpoint parameter construction;
- document id extraction;
- title extraction;
- empty-day interpretation;
- whether PDF endpoints are recorded as metadata-only URLs.

## Rejection Pattern: BOP_ALMERIA

`BOP_ALMERIA` remains `inventory_only`.

The evaluated official surface resolves to:

```text
https://app.dipalme.org/bop/publico.zul
```

That surface is a ZK/JavaScript application. It does not expose the same kind of deterministic,
server-rendered metadata listing used by the accepted pilots.

Reject or defer a provincial source when:

- metadata requires browser-side JavaScript execution;
- the page is a framework shell without announcement records in the initial payload;
- the source requires PDF download to discover title/date/document URL;
- login, CAPTCHA, or session-specific workflows are required;
- the only stable path is a complex backing protocol not yet audited;
- preview cannot be scoped to one source and one date/current bulletin safely;
- the parser would need brittle browser automation before basic endpoint discovery is complete.

Rejected does not mean non-official. It means unsuitable for the current deterministic
metadata-only HTML monitor.

## Next-Source Selection Criteria

For future provincial sources, prefer sources that meet most or all of these:

- official landing URL is verified in `config/sources.yaml`;
- listing is accessible without login;
- listing metadata is present in server-returned HTML or a clear official backing endpoint;
- no mandatory JS rendering for metadata discovery;
- no PDF download required to discover title/date/official URL;
- one-source, one-date or one-current-bulletin preview is possible;
- document identifiers are visible or derivable from stable fields;
- official URL is stable and deterministic;
- empty days return a safe empty result rather than an ambiguous failure;
- parser can be kept small and covered by a fixture;
- live preview without `--write` returns either 0 safely or at least 1 record on an active day.

For selection, prefer date-bounded sources over current-only sources. Current-only sources can be
useful for coverage observation, but they should not be mistaken for backfill-ready monitors.

## Recommended Next Task

Recommended next task:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-003
```

Boundary:

- evaluate at most 2 more provincial sources;
- use the criteria above before selecting;
- do not bulk-monitor provincial sources;
- keep preview-first semantics;
- do not use `--write`;
- do not create candidates/evidence;
- do not download PDFs/artifacts;
- do not touch downstream repos.

Do not open `TASK-SOURCE-HTML-MONITOR-HELPERS-001` yet. The current shared helpers are sufficient.
Open that helper task only if the next two sources show repeated duplication that is not already
covered by the existing record/date/hash helpers.

## Safety Confirmation

Confirmed by scope:

- no parser behavior changed;
- no new sources were added;
- no monitor was run for this report;
- no HTML/RSS/API JSONL writes were run;
- no `source_candidates` were created;
- no evidence-grade records were created;
- no PDFs or artifacts were downloaded;
- no downstream repositories were touched;
- no backfills were run;
- no broad/all-source discovery was run;
- no VPS or production DB operations were run;
- no LLM classification was added.

# Spanish Public Info Radar MCP review - 2026-05-21

## Scope

This report reviews `https://github.com/mjgmario/spanish-public-info-radar-mcp` as a technical
reference for `official-sources`.

External repository snapshot reviewed:

```text
spanish-public-info-radar-mcp commit: 7b059e5e7e652f2c72c87d84d8a9b2186fd1e643
```

Files reviewed:

- `src/public_radar/sources/bdns.py`
- `src/public_radar/sources/boe.py`
- `src/public_radar/sources/ine.py`
- `src/public_radar/sources/datos_gob.py`
- `src/public_radar/common/http.py`
- `src/public_radar/mcp/server.py`
- `src/public_radar/prompts/`
- `tests/unit/test_bdns_parser.py`
- `tests/unit/test_boe_parser.py`
- `tests/unit/test_datos_gob_parser.py`
- `tests/unit/test_http.py`
- `tests/unit/test_mcp_prompts.py`
- `tests/unit/test_mcp_tools.py`
- `tests/integration/`
- `README.md`
- `LICENSE`

No code was copied. No architecture, database, source adapter, MCP tool, or downstream integration
changes were made.

The local helper router was not used because this task required external repository review and
cross-file reasoning, which are explicitly outside the eligible helper task types.

## Executive conclusion

The repository is useful as a reference, but not as a replacement architecture.

The highest-value idea for `official-sources` is BDNS. BDNS is a primary grants/subsidies source,
while the current `official-sources` model is bulletin/evidence oriented across BOE, BOJA, DOGV,
and BOCM. A BDNS adapter could improve `EduAyudas`, `la-ayuda`, and subsidy-oriented downstream
work because it would query the grant registry directly instead of relying only on bulletin
metadata and candidate prefilters.

The second useful area is MCP ergonomics: small tool handlers, source-specific response shaping,
and discoverable prompt templates. This can inform future read-only MCP improvements, but it must
be adapted to the local cache-first, evidence-first boundary.

The third useful area is practical API hardening: endpoint quirks, schema variation, partial
results, 404 handling, and parser tests. `official-sources` already has stricter audit,
hashing, retry, and storage guarantees, so the external repo should be treated as prior art for
source behavior, not as implementation code to import.

## Repository model compared with official-sources

| Area | spanish-public-info-radar-mcp | official-sources implication |
| --- | --- | --- |
| Runtime model | Live API calls on each MCP tool invocation | Do not replace cache-first evidence storage |
| Storage | No local DB | Keep SQLite, hashes, migrations, evidence review |
| MCP | Tool layer owns live retrieval workflows | Keep MCP read-only over stored evidence unless a separate live-query task is approved |
| Source modules | One client/parser module per public API | Compatible with local source adapter pattern |
| Output shape | Tool-specific JSON optimized for model use | Reuse the idea, but preserve local citation/integrity envelopes |
| Prompts | Large prompt registry exposed through `prompts/list` | Useful as UX pattern, but prompts must respect local non-publication and no-write rules |
| Error behavior | Tool handlers return structured `error` fields | Compatible with cache-miss / no-publication semantics |
| Tests | Unit tests for parser, HTTP, MCP tools/prompts; integration tests for live APIs | Useful pattern for any BDNS adapter audit |

## Reusable ideas

### 1. BDNS as a source candidate

`sources/bdns.py` is the strongest reference in the repo. It models two different BDNS domains:

- `convocatorias`, via `/convocatorias/ultimas` when no filters are present and
  `/convocatorias/busqueda` when filters are present.
- `concesiones`, via `/concesiones/busqueda`.

Practical details worth auditing for local use:

- BDNS date parameters are normalized to Spanish date format before request dispatch.
- Response pagination handles both older `items` and newer `content` shapes.
- Convocatoria IDs may appear under `codigoBdns`, `codigo`, or `id`.
- Concesion IDs may appear under `idConcesion`, `id`, or `codigo`.
- Amounts are parsed with `Decimal`, which is important for grants.
- Source records preserve `raw_data`, which maps well to the local raw metadata/hash model.

Local adaptation should not copy the module. A local BDNS task should define:

- source identity and hierarchy: BDNS is not a bulletin, but it is an official registry;
- whether BDNS records become `official_documents`, a separate grants table, or a new source
  evidence table;
- raw payload hashing before parsing;
- stable external IDs for convocatoria and concesion records;
- date/range limits and operational safety rules;
- whether BDNS ingestion is scheduled, manual, or query-only;
- candidate/evidence review boundaries for downstream projects.

### 2. Source-specific parsers instead of a unified public-data abstraction

The external repo does not force all sources into a single generic schema. BDNS, BOE/BORME, INE,
and datos.gob.es each return shaped outputs that fit their domain.

That matches the direction already visible in `official-sources`:

- BOE daily summaries and consolidated legislation are separate concepts.
- BOJA, DOGV, and BOCM have source-specific ingestion/parser behavior.
- Local storage preserves raw metadata and source snapshot hashes.

For future sources, keep the source-specific adapter approach. A generic "public data item" layer
would hide important source semantics and weaken evidence quality.

### 3. MCP prompts as reusable workflow affordances

The external repo exposes prompt definitions through MCP, not just tools. The prompt modules map
named workflows to tool calls, with arguments and descriptions discoverable by clients.

This is worth considering for `official-sources`, but with a narrower scope:

- prompts should describe read-only evidence retrieval workflows;
- prompts should not imply legal interpretation, approval, publication, or downstream writes;
- prompts should surface cache-miss behavior and recommended operational commands rather than
  silently fetching live data;
- prompts should be source-aware, for example BOE evidence review, consolidated law citation,
  candidate trace, or integrity status.

Good first local prompt candidates:

- `boe_document_evidence_review`
- `source_trace_for_candidate`
- `consolidated_law_block_citation`
- `integrity_status_for_document`
- future `bdns_convocatoria_evidence_review` if BDNS is added.

### 4. API edge-case documentation in code and tests

The BOE module documents and handles concrete API behavior:

- BOE consolidated search is JSON.
- Full text and block endpoints are XML-only.
- Empty `query` parameters may trigger BOE API failures, so the client omits them.
- BORME summary shapes vary between direct section items and nested `emisor` items.
- XML is converted recursively while preserving attributes and repeated tags.

`official-sources` already has a stronger BOE policy for retries, throttle, no-publication, raw
hashes, and cached consolidated blocks. The reusable point is not the exact parser. The reusable
point is to keep every observed API quirk captured in source-local tests and reports.

### 5. Tool-level error envelopes

The external MCP handlers catch expected source failures and return structured `error` responses
instead of exposing stack traces to the model. This aligns with local `cache_miss`,
`no_publication`, and read-only MCP constraints.

For `official-sources`, the preferred model remains:

- local query miss: structured `cache_miss`;
- controlled official no-publication condition: structured `no_publication`;
- upstream or parser failure during operational ingestion: recorded in `ingestion_runs`;
- MCP response: readable and bounded, with no raw traceback.

## Ideas that do not fit directly

### Live API calls from MCP tools

The external repo is intentionally on-the-fly. `official-sources` is intentionally cache-first:

```text
official source -> ingestion -> normalized document -> citation -> integrity check -> candidate extraction -> human review
```

Live MCP tools would bypass local evidence controls unless designed as a separate mode. They
should not be added casually because they would weaken:

- reproducibility;
- raw payload hashing;
- evidence review;
- rate-limit audit fields;
- downstream import contracts;
- no automatic publication boundaries.

### One public MCP surface for broad data exploration

The external server is designed for broad public-data querying. `official-sources` is a private
evidence infrastructure layer. It has no authentication and the docs already say MCP must remain
private. Any broad query/public access product should be a separate project or a later authenticated
API task, not an expansion of the current MCP surface.

### Large prompt catalog before stable tool semantics

The external repo has many prompts, including cross-source research workflows. That is useful for a
consultative MCP server, but too broad for `official-sources` today. Local prompts should follow
implemented tools and storage semantics, not pre-announce future capabilities.

### Direct reuse of BOE code

The BOE overlap is low value. `official-sources` already has:

- BOE daily summary ingestion;
- controlled no-publication handling;
- conservative HTTP policy with retry/backoff audit fields;
- raw payload hashing;
- artifact caching;
- consolidated legislation, index, block retrieval, and citation;
- read-only MCP over stored data.

The external BOE code is still useful for observed endpoint quirks, but not as a source of local
implementation.

## BDNS assessment

BDNS deserves a dedicated audit task.

Reasons:

- It is a primary source for grants and subsidies, not just a bulletin mention.
- It could reduce false positives from bulletin keyword prefilters.
- It provides structured amounts, granting bodies, beneficiary/concession records, and deadlines.
- It maps directly to downstream subsidy workflows.
- The external repo already identifies concrete parser hazards worth verifying against the live
  official API.

Open design questions before implementation:

- Should BDNS be modeled as an official source under the same `official_documents` table, or should
  grants and awards use separate domain tables?
- What is the stable evidence unit: convocatoria, concesion, or both?
- What raw payloads must be stored and hashed for traceability?
- Which URLs count as official evidence when BDNS links to BOE or regional bases?
- How should candidate profiles combine BOE/BOJA/DOGV/BOCM bulletin evidence with BDNS registry
  records?
- Should BDNS ingestion be scheduled, date-windowed, or manual only at first?

Recommendation:

```text
TASK-BDNS-001 - BDNS source audit and adapter strategy
```

Start with no implementation. The first task should produce a local source audit, endpoint matrix,
data model recommendation, and fixture set plan.

## MCP tools and prompts assessment

`official-sources` should improve MCP prompts, but only after preserving local boundaries.

Current local MCP docs emphasize:

- read-only tools;
- no live fetch;
- no arbitrary downloads;
- no downstream mutation;
- no automatic approval or publication;
- private/local MCP exposure.

The external prompt registry proves that MCP prompts can make tool workflows easier to discover.
The local version should be smaller and evidence-focused.

Recommendation:

```text
TASK-MCP-PRM-001 - Read-only MCP prompt templates for official-sources
```

Possible scope:

- add prompt definitions for existing implemented MCP tools only;
- document prompt safety rules in `docs/MCP_TOOLS.md`;
- add prompt unit tests similar to `test_mcp_prompts.py`;
- do not add live source tools;
- do not add broad legal-analysis prompts.

Priority: useful, but lower than BDNS if the immediate goal is subsidy coverage.

## HTTP and error-handling assessment

The external repo uses `tenacity` over `httpx` with 3 attempts for timeouts/network errors, and
turns 404 into a `NotFoundError`.

`official-sources` is already stricter for BOE-like operational ingestion:

- finite retry policy for 429, 500, 502, 503, and 504;
- `Retry-After` support;
- throttle audit fields;
- persisted retry counts;
- status separation between summary ingestion and artifact downloads;
- source-specific no-publication semantics.

Reusable idea:

- keep a shared request-policy abstraction, but source-specific enough to record correct audit
  semantics.

Do not import the external HTTP layer. It is simpler than the local requirements and does not
persist enough operational evidence.

## datos.gob.es and INE assessment

These modules are useful as references for schema variability and API breadth, but they are lower
priority for current `official-sources` goals.

datos.gob.es is valuable if a downstream product needs catalog discovery, but it is metadata about
datasets, not direct grant/legal evidence. INE is useful for statistics context, but it does not
fit the current citation/integrity/candidate review workflow as directly as BDNS.

Recommendation:

- keep both as prior-art references only;
- do not add them to `official-sources` until a downstream project has a concrete evidence use
  case.

## License and copying risk

The external repository includes a `LICENSE` file using MIT-style terms plus an explicit visible
attribution requirement:

```text
Based on Spanish Public Data MCP by Mario Jimenez Gutierrez
```

Implications:

- It is acceptable to learn from the architecture and behavior.
- Do not copy code into `official-sources` without a deliberate license review.
- If code is reused or derivative implementation is created from copied portions, attribution must
  be added where required.
- The safest path is clean-room implementation from official API docs and local tests, using this
  repository only as prior art and checklist material.

## Recommended next tasks

### Highest priority

```text
TASK-BDNS-001 - BDNS source audit and adapter strategy
```

Deliverables:

- official BDNS API endpoint matrix;
- live/non-live request policy recommendation;
- raw payload/hash strategy;
- stable identifier strategy for convocatorias and concesiones;
- proposed storage model;
- fixture plan;
- no code implementation unless explicitly approved after the audit.

### Medium priority

```text
TASK-MCP-PRM-001 - Read-only MCP prompt templates for official-sources
```

Deliverables:

- prompts for existing MCP tools only;
- prompt safety rules;
- unit tests for prompt registry and generated prompt content;
- documentation update in `docs/MCP_TOOLS.md`.

### Lower priority

```text
TASK-BOE-CONSOLIDATED-SEARCH-REVIEW - Revisit BOE consolidated legislation search
```

Only open this if search is required by a downstream workflow. The current local model deliberately
implements identifier/index/block retrieval without broad search.

```text
TASK-DATOS-GOB-REFERENCE - datos.gob.es source relevance review
TASK-INE-REFERENCE - INE source relevance review
```

Keep both blocked until a concrete downstream evidence use case exists.

## Final decision

Open `TASK-BDNS-001`.

Also open `TASK-MCP-PRM-001` if MCP discoverability becomes a near-term goal, but do not let prompt
work expand the MCP server beyond read-only local evidence retrieval.

Do not replace the `official-sources` architecture with the external repo's live-query architecture.
The useful overlap is source/API hardening, BDNS research, and prompt/tool ergonomics.

# Source coverage v1.1 snapshot - 2026-05-24

Task: `TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001`

## Scope

This is a reporting/control-plane snapshot generated after adding the BOPV metadata-only REST/API
discovery adapter.

Source of truth:

```text
config/sources.yaml
```

This report does not add sources, ingestion behavior, candidates, evidence, artifacts, backfills,
RSS/API writes, downstream writes, VPS operations, production DB operations, or LLM classification.

## Registry Summary

Total registered executable sources: 22.

Counts by `jurisdiction_level`:

| jurisdiction_level | count |
| --- | ---: |
| `autonómica` | 19 |
| `estatal` | 2 |
| `european` | 1 |

Counts by `operational_status`:

| operational_status | count |
| --- | ---: |
| `metadata_adapter_validated` | 9 |
| `inventory_only` | 12 |
| `paused` | 1 |

Counts by `monitor_support`:

| monitor_support | count |
| --- | ---: |
| `available` | 9 |
| `none` | 12 |
| `planned` | 1 |

Counts by `backfill_support`:

| backfill_support | count |
| --- | ---: |
| `validated` | 6 |
| `planned` | 3 |
| `available` | 1 |
| `none` | 12 |

Counts by `evidence_adapter`:

| evidence_adapter | count |
| --- | ---: |
| `true` | 6 |
| `false` | 16 |

Counts by `candidate_creation_allowed`:

| candidate_creation_allowed | count |
| --- | ---: |
| `false` | 22 |

Counts by `evidence_grade_allowed`:

| evidence_grade_allowed | count |
| --- | ---: |
| `false` | 22 |

No current registry entry is authorized for automatic candidate creation or evidence-grade
promotion.

## Discovery Monitor Summary

Validated RSS/Atom discovery monitor sources:

| source_code | feed_type | feed_url | role |
| --- | --- | --- | --- |
| `BOE` | `rss` | `https://www.boe.es/rss/boe.php` | State/control source |
| `BOJA` | `atom` | `https://www.juntadeandalucia.es/boja/distribucion/boja.xml` | Autonomous expansion source |
| `BOCYL` | `rss` | `https://bocyl.jcyl.es/rss.do` | First autonomous bulletin pilot |

Validated API discovery monitor sources:

| source_code | endpoint | role |
| --- | --- | --- |
| `BOPV` | `https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}` | First API discovery source |

RSS/API discovery records remain metadata-only:

```text
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

Inventory-only sources:

```text
DOUE
BOPA
BOIB
BOC_CANARIAS
BOC_CANTABRIA
DOCM
DOE
DOG
BOR
BON
BOCCE
BOME
```

Paused source:

```text
BOCM
```

Metadata adapter validated sources:

```text
BOE
BDNS
BOJA
BOA
BOCYL
DOGC
BORM
BOPV
DOGV
```

Sources needing future API/RSS/HTML investigation:

- `DOUE`, `BOPA`, `BOIB`, `BOC_CANARIAS`, `BOC_CANTABRIA`, `DOCM`, `DOE`, `DOG`, `BOR`,
  `BON`, `BOCCE`, and `BOME`: registry coverage exists, but no validated access method exists in
  `config/sources.yaml`.
- `BOCM`: keep paused until endpoint/connectivity instability is resolved.
- `DOGC`: existing metadata support uses REST endpoints; no stable official RSS/Atom feed was
  verified during RSS expansion.
- `BDNS`, `BOA`, `DOGC`, `DOGV`, and `BORM`: validated access methods exist, but they are not part
  of the generic RSS/API discovery monitor line unless a future task explicitly scopes them.

## MCP Coverage Summary

Available read-only MCP coverage tools:

| tool | exposes |
| --- | --- |
| `list_sources` | Source code, name, jurisdiction level, operational status, monitor support, evidence adapter flag |
| `get_source_status` | Full registry entry for one source and safety flags |
| `list_monitorable_sources` | Sources with registry-declared monitor-capable access methods |
| `list_latest_discovery_entries` | Existing metadata-only RSS discovery JSONL, if present |

Current MCP coverage can expose BOPV as monitorable because `config/sources.yaml` now includes a
validated `api` access method for BOPV.

Current MCP latest-discovery reading is still RSS-output specific:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

API discovery output is not yet exposed through `list_latest_discovery_entries`:

```text
data/api_monitor/BOPV/<YYYY-MM-DD>/api_discovery.jsonl
```

That should remain a separate read-only task:

```text
TASK-MCP-API-DISCOVERY-OUTPUT-001
```

The MCP coverage tools explicitly do not:

- fetch live RSS/Atom/API feeds;
- create files;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- run backfills;
- write downstream repositories;
- publish data.

## Safety Boundaries

Confirmed v1.1 boundaries:

- RSS/API discovery is metadata-only.
- MCP source coverage is read-only.
- Candidate creation is disabled for all 22 current entries.
- Evidence-grade promotion is disabled for all 22 current entries.
- PDF/artifact download remains out of discovery and coverage reporting.
- Downstream writes remain out of `official-sources`.
- Broad/all-source monitor runs remain blocked.

## Coverage V1.1 Assessment

The project now meets the v1.1 source-coverage milestone:

- an executable source registry exists;
- the registry covers 22 sources;
- three RSS/Atom discovery sources exist: `BOE`, `BOJA`, and `BOCYL`;
- one API discovery source exists: `BOPV`;
- MCP can expose registry coverage and read existing RSS discovery output;
- MCP API discovery output reading is explicitly identified as future work;
- safety flags keep candidates and evidence-grade disabled by default;
- downstream/product coupling is still excluded.

This remains a coverage platform milestone, not an evidence platform expansion.

## Next Recommended Tasks

Recommended next tasks:

1. `TASK-MCP-API-DISCOVERY-OUTPUT-001` - add read-only MCP access to existing API monitor JSONL
   output if API discovery samples need to be visible through MCP.
2. `TASK-SOURCE-RSS-MONITOR-003` - only after choosing 2-3 verified official RSS/Atom feeds.
3. `TASK-SOURCE-HTML-MONITOR-PILOT-001` - only for sources without RSS/API, and only after a
   source-specific endpoint/robots/fixture audit.

Do not expand candidates or evidence-grade workflows until explicitly approved.

## Guardrail Confirmation

This snapshot did not create:

- `source_candidates`;
- evidence-grade records;
- PDFs;
- artifact files;
- downstream product writes;
- backfills;
- RSS JSONL writes;
- API JSONL writes;
- VPS operations;
- production DB operations;
- LLM classification.

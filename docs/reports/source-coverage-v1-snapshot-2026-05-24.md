# Source coverage v1 snapshot - 2026-05-24

Task: `TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001`

## Scope

This is a reporting/control-plane snapshot generated from the executable source registry and the
current read-only monitor/MCP capabilities.

Source of truth:

```text
config/sources.yaml
```

This report does not add sources, ingestion, candidates, evidence, artifacts, backfills, downstream
writes, VPS operations, production DB operations, or LLM classification.

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

## Monitor Summary

Validated RSS/Atom discovery sources:

| source_code | feed_type | feed_url | role |
| --- | --- | --- | --- |
| `BOCYL` | `rss` | `https://bocyl.jcyl.es/rss.do` | First autonomous bulletin pilot |
| `BOE` | `rss` | `https://www.boe.es/rss/boe.php` | State/control source |
| `BOJA` | `atom` | `https://www.juntadeandalucia.es/boja/distribucion/boja.xml` | Autonomous expansion source |

RSS/Atom discovery remains metadata-only:

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

Sources needing API-specific or non-RSS follow-up:

- `BOPV`: keep as `TASK-SOURCE-BOPV-API-001`; its current validated access methods are HTML/XML
  issue discovery surfaces, not a generic RSS expansion path.
- `DOGC`: no stable official RSS/Atom feed was verified during RSS expansion; existing support is
  through REST metadata endpoints.

## MCP Coverage Summary

Available read-only MCP coverage tools:

| tool | exposes |
| --- | --- |
| `list_sources` | Source code, name, jurisdiction level, operational status, monitor support, evidence adapter flag |
| `get_source_status` | Full registry entry for one source and safety flags |
| `list_monitorable_sources` | Sources with registry-declared monitor-capable access methods |
| `list_latest_discovery_entries` | Existing metadata-only RSS discovery JSONL, if present |

The MCP coverage tools explicitly do not:

- fetch live RSS/Atom feeds;
- create files;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- run backfills;
- write downstream repositories;
- publish data.

## Safety Boundaries

Confirmed v1 boundaries:

- RSS/Atom is discovery-only.
- MCP source coverage is read-only.
- Candidate creation is disabled for all 22 current entries.
- Evidence-grade promotion is disabled for all 22 current entries.
- PDF/artifact download remains out of discovery and coverage reporting.
- Downstream writes remain out of `official-sources`.
- Broad/all-source monitor runs remain blocked.

## Coverage V1 Assessment

The project now meets a first useful source-coverage milestone:

- an executable source registry exists;
- the registry covers 22 sources;
- at least one autonomous bulletin has RSS discovery (`BOCYL`);
- a state/control RSS source exists (`BOE`);
- a second autonomous source has Atom discovery (`BOJA`);
- MCP can expose registry coverage and read existing discovery output;
- safety flags keep candidates and evidence-grade disabled by default;
- downstream/product coupling is still excluded.

This is a coverage platform milestone, not an evidence platform expansion. Current RSS/Atom output
is suitable for discovery and coverage reporting only.

## Next Recommended Tasks

Recommended next tasks:

1. `TASK-SOURCE-BOPV-API-001` - BOPV REST/API discovery adapter.
2. `TASK-SOURCE-RSS-MONITOR-003` - only after choosing 2-3 verified official RSS/Atom feeds.
3. `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` - if sample discovery outputs are needed for demos or
   downstream planning.

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
- VPS operations;
- production DB operations;
- LLM classification.

# Source coverage v1.2 snapshot - 2026-05-24

Task: `TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001`

## Scope

This is a reporting/control-plane snapshot generated after `TASK-SOURCE-RSS-MONITOR-003` was
merged to `main`.

Current integrated commit:

```text
d2afbfd feat: expand RSS discovery monitor sources
```

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
| `inventory_only` | 9 |
| `metadata_adapter_validated` | 9 |
| `monitor_validated` | 3 |
| `paused` | 1 |

Counts by `monitor_support`:

| monitor_support | count |
| --- | ---: |
| `available` | 12 |
| `none` | 9 |
| `planned` | 1 |

Counts by `backfill_support`:

| backfill_support | count |
| --- | ---: |
| `available` | 1 |
| `none` | 12 |
| `planned` | 3 |
| `validated` | 6 |

Counts by `evidence_adapter`:

| evidence_adapter | count |
| --- | ---: |
| `false` | 16 |
| `true` | 6 |

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

| source_code | feed_type | feed_url | notes |
| --- | --- | --- | --- |
| `BOE` | `rss` | `https://www.boe.es/rss/boe.php` | State/control source |
| `BOJA` | `atom` | `https://www.juntadeandalucia.es/boja/distribucion/boja.xml` | Complete BOJA web feed |
| `BOCYL` | `rss` | `https://bocyl.jcyl.es/rss.do` | First autonomous bulletin RSS pilot |
| `BOIB` | `rss` | `https://www.caib.es/eboibfront/es/rss` | Official BOIB RSS feed |
| `BOC_CANTABRIA` | `rss` | `https://www.cantabria.es/o/BOC/feed/6802081` | Official category feed; not complete bulletin coverage |
| `DOE` | `rss` | `https://doe.juntaex.es/rss/rss.php?seccion=6` | Official `SUMARIO COMPLETO` RSS endpoint |

Validated API discovery monitor sources:

| source_code | endpoint | notes |
| --- | --- | --- |
| `BOPV` | `https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}` | Official Open Data Euskadi BOPV REST endpoint |

Important caveats:

- `BOC_CANTABRIA` is official but category-scoped, not complete bulletin coverage.
- `DOE` feed is valid, but the live preview for RSS-003 returned `records=0`.
- `DOGC` and `BON` were not added because tested feed candidates returned 404.

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
BOC_CANARIAS
DOCM
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

Monitor-validated-only sources:

```text
BOIB
BOC_CANTABRIA
DOE
```

## MCP Coverage Summary

Available read-only MCP coverage tools:

| tool | exposes |
| --- | --- |
| `list_sources` | Source code, name, jurisdiction level, operational status, monitor support, evidence adapter flag |
| `get_source_status` | Full registry entry for one source and safety flags |
| `list_monitorable_sources` | Sources with registry-declared monitor-capable access methods |
| `list_latest_discovery_entries` | Existing metadata-only RSS/API discovery JSONL, if present |

`list_latest_discovery_entries` reads existing files only:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
```

MCP coverage does not fetch live RSS/API sources and does not create files.

## Safety Boundaries

Confirmed v1.2 boundaries:

- RSS/API discovery is metadata-only.
- MCP source coverage is read-only.
- Candidate creation is disabled for all 22 current entries.
- Evidence-grade promotion is disabled for all 22 current entries.
- PDF/artifact download remains out of discovery and coverage reporting.
- Downstream writes remain out of `official-sources`.
- Broad/all-source monitor runs remain blocked.
- JSONL output requires explicit `--write`.

## Coverage V1.2 Assessment

The project now meets the v1.2 source-coverage milestone:

- an executable source registry exists;
- the registry covers 22 sources;
- six RSS/Atom monitor-capable sources exist: `BOE`, `BOJA`, `BOCYL`, `BOIB`,
  `BOC_CANTABRIA`, and `DOE`;
- one API monitor-capable source exists: `BOPV`;
- MCP can expose registry coverage and read existing RSS/API discovery output;
- a controlled run plan exists for one-source-at-a-time monitor operation;
- safety flags keep candidates and evidence-grade disabled by default;
- downstream/product coupling is still excluded.

This remains a coverage platform milestone, not an evidence platform expansion.

## Next Recommended Tasks

Recommended next tasks:

1. `TASK-SOURCE-RSS-MONITOR-004` - only after verifying another 2-3 official stable RSS/Atom
   feeds.
2. `TASK-SOURCE-HTML-MONITOR-PILOT-001` - for sources without RSS/API, only after a
   source-specific endpoint/robots/fixture audit.
3. `TASK-SOURCE-COVERAGE-RUN-REPORT-001` - if actual metadata-only JSONL writes are run.

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
- all-source runs;
- VPS operations;
- production DB operations;
- LLM classification.

## Validation

Read-only CLI sanity was run for:

```bash
official-sources sources list
official-sources sources status --source BOIB
official-sources sources status --source BOC_CANTABRIA
official-sources sources status --source DOE
```

The global `official-sources` console script in this environment is stale and showed the pre-RSS-003
registry state for `BOIB`, `BOC_CANTABRIA`, and `DOE`. The source-tree entrypoint was then used to
validate the integrated code and registry:

```powershell
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" sources list
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" sources status --source BOIB
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" sources status --source BOC_CANTABRIA
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" sources status --source DOE
```

Source-tree CLI sanity results:

```text
BOIB: operational_status=monitor_validated monitor_support=available
BOC_CANTABRIA: operational_status=monitor_validated monitor_support=available
DOE: operational_status=monitor_validated monitor_support=available
```

No RSS/API monitor command was run and no JSONL output was written for this snapshot.

# Source coverage v1.5 snapshot - 2026-05-26

Task: `TASK-SOURCE-COVERAGE-V1.5-SNAPSHOT-001`

## Scope

This is a reporting/control-plane snapshot after `TASK-SOURCE-PROVINCIAL-DISCOVERY-002`.

Current integrated commit:

```text
8f31062 feat: expand provincial HTML discovery monitors
```

Source of truth:

```text
config/sources.yaml
```

This report does not add sources, ingestion behavior, candidates, evidence, artifacts, backfills,
RSS/API/HTML writes, downstream writes, VPS operations, production DB operations, or LLM
classification.

## Registry Totals

Total registered executable sources: 65.

Counts by `jurisdiction_level`:

| jurisdiction_level | count |
| --- | ---: |
| `estatal` | 2 |
| `european` | 1 |
| `autonomica` | 19 |
| `provincial` | 43 |

Counts by `operational_status`:

| operational_status | count |
| --- | ---: |
| `inventory_only` | 49 |
| `metadata_adapter_validated` | 9 |
| `monitor_validated` | 6 |
| `paused` | 1 |

Counts by `monitor_support`:

| monitor_support | count |
| --- | ---: |
| `available` | 15 |
| `none` | 49 |
| `planned` | 1 |

Counts by `backfill_support`:

| backfill_support | count |
| --- | ---: |
| `available` | 1 |
| `none` | 55 |
| `planned` | 3 |
| `validated` | 6 |

Counts by `evidence_adapter`:

| evidence_adapter | count |
| --- | ---: |
| `false` | 59 |
| `true` | 6 |

Counts by `candidate_creation_allowed`:

| candidate_creation_allowed | count |
| --- | ---: |
| `false` | 65 |

Counts by `evidence_grade_allowed`:

| evidence_grade_allowed | count |
| --- | ---: |
| `false` | 65 |

No current registry entry is authorized for automatic candidate creation or evidence-grade
promotion.

## Discovery Coverage

RSS/Atom metadata-only discovery sources:

| source_code | access type | notes |
| --- | --- | --- |
| `BOE` | `rss` | State/control source |
| `BOJA` | `atom` | Complete BOJA web feed |
| `BOCYL` | `rss` | First autonomous bulletin RSS pilot |
| `BOIB` | `rss` | Official BOIB feed |
| `BOC_CANTABRIA` | `rss` | Official category feed; not complete bulletin coverage |
| `DOE` | `rss` | Official DOE feed; RSS-003 preview returned zero records |

API metadata-only discovery source:

| source_code | endpoint |
| --- | --- |
| `BOPV` | `https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}` |

HTML metadata-only discovery sources:

| source_code | endpoint | notes |
| --- | --- | --- |
| `BOP_A_CORUNA` | `https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}` | First provincial HTML pilot |
| `BOP_ALBACETE` | `https://bop.dipualba.es` | Current-bulletin HTML summary; page links are metadata-only and are not downloaded |
| `BOP_ALICANTE` | `https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php` | Official consultation-page backing endpoint, queried one date at a time |

Current discovery-family summary:

```text
RSS/Atom discovery: 6 sources
API discovery: 1 source
HTML provincial discovery: 3 sources
```

## Provincial Discovery 002 Summary

`TASK-SOURCE-PROVINCIAL-DISCOVERY-002` evaluated the first deterministic MCP recommendations:

```text
BOP_ALBACETE
BOP_ALICANTE
BOP_ALMERIA
```

Selected:

```text
BOP_ALBACETE -> monitor_validated
BOP_ALICANTE -> monitor_validated
```

Rejected:

```text
BOP_ALMERIA -> inventory_only
```

Reason for rejection:

```text
The tested official BOP Almeria surface resolves to a ZK/JavaScript application and is not a clean
deterministic HTML metadata page for the current monitor.
```

Live preview results from the implementation task:

```text
BOP_ALBACETE: command_started=html monitor source_code=BOP_ALBACETE date=2026-05-25 mode=preview records=1 discovery_metadata_only=true
BOP_ALICANTE: command_started=html monitor source_code=BOP_ALICANTE date=2026-05-25 mode=preview records=1 discovery_metadata_only=true
```

No `data/html_monitor/` output was created because `--write` was not used.

## MCP Coverage

The MCP coverage surface can expose:

- `list_sources`
- `get_source_status`
- `list_monitorable_sources`
- `list_latest_discovery_entries`
- `preview_discovery`
- `recommend_next_sources`

`list_monitorable_sources` now includes the three provincial HTML discovery sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
```

`list_latest_discovery_entries` reads existing RSS/API/HTML JSONL only. It does not fetch live
sources and does not write files.

`preview_discovery` may run a controlled one-source preview for validated RSS/API/HTML sources, but
it does not write JSONL or mutate state.

`recommend_next_sources` is deterministic and excludes already monitored provincial sources. After
this snapshot, `BOP_ALBACETE` and `BOP_ALICANTE` should no longer appear in the recommendation list.

## Safety Boundaries

Confirmed:

- RSS/API/HTML discovery is metadata-only;
- MCP cache readback is read-only;
- MCP recommendations do not fetch live sources or execute previews;
- CLI monitor commands remain one-source-at-a-time;
- `inventory_only` entries are not monitored;
- `--write` remains required for JSONL output;
- no automatic `source_candidates`;
- no automatic evidence-grade promotion;
- no PDF/artifact download;
- no downstream writes;
- no broad/all-source monitor runs;
- no backfills;
- no VPS or production DB operations;
- no LLM classification.

## Coverage v1.5 Assessment

The platform now has:

- an executable registry with 65 official source entries;
- 6 RSS/Atom metadata-only discovery sources;
- 1 API metadata-only discovery source;
- 3 HTML provincial metadata-only discovery sources;
- 40 remaining provincial inventory-only sources;
- read-only MCP coverage and cache-readback tools;
- controlled MCP one-source previews;
- deterministic MCP next-source recommendations;
- no downstream/product coupling from registry or discovery work.

This snapshot confirms that `BOP_A_CORUNA` was not a one-off. The provincial HTML discovery pattern
can be extended, but `BOP_ALMERIA` shows that not every provincial bulletin fits a simple
deterministic HTML parser.

## Next Recommended Tasks

Recommended next task:

```text
TASK-SOURCE-PROVINCIAL-PATTERN-REPORT-001
```

Purpose:

```text
Compare BOP_A_CORUNA, BOP_ALBACETE, and BOP_ALICANTE to decide whether a reusable provincial HTML
abstraction exists or source-specific adapters remain the correct approach.
```

Only after that report, consider:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-003
```

Boundary:

- evaluate at most 2 more provincial sources;
- no bulk provincial monitoring;
- preview first;
- no JSONL writes unless explicitly authorized;
- no candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS/prod DB,
  or LLM classification.

## Validation

Commands run for the integrated implementation before this snapshot:

```text
python -m ruff check src tests
python -m pytest -q
git diff --check
```

Results:

```text
ruff: OK
pytest: 532 passed, 1 warning
git diff --check: OK
```

Snapshot sanity commands:

```text
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_ALBACETE
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_ALICANTE
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_ALMERIA
```

Results:

```text
BOP_ALBACETE: operational_status=monitor_validated monitor_support=available
BOP_ALICANTE: operational_status=monitor_validated monitor_support=available
BOP_ALMERIA: operational_status=inventory_only monitor_support=none
```

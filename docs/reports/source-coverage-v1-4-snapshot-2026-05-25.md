# Source coverage v1.4 snapshot - 2026-05-25

Task: `TASK-SOURCE-COVERAGE-V1.4-SNAPSHOT-001`

## Scope

This is a reporting/control-plane snapshot after `TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001`.

Current integrated commit:

```text
bca05bb feat: add provincial HTML discovery pilot
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
| `autonómica` | 19 |
| `provincial` | 43 |

Counts by `operational_status`:

| operational_status | count |
| --- | ---: |
| `inventory_only` | 51 |
| `metadata_adapter_validated` | 9 |
| `monitor_validated` | 4 |
| `paused` | 1 |

Counts by `monitor_support`:

| monitor_support | count |
| --- | ---: |
| `available` | 13 |
| `none` | 51 |
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

HTML metadata-only discovery source:

| source_code | endpoint | notes |
| --- | --- | --- |
| `BOP_A_CORUNA` | `https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}` | First provincial HTML pilot |

`BOP_A_CORUNA` is the only provincial source promoted by this task. The remaining 42 provincial
entries remain inventory-only.

## Provincial Pilot Summary

`TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001` proved that one provincial bulletin can be observed
without downloading PDFs or creating downstream candidate/evidence records.

Live preview result:

```text
command_started=html monitor source_code=BOP_A_CORUNA date=2026-05-25 mode=preview records=1 discovery_metadata_only=true
document_id=2026/3193
official_url=https://bop.dacoruna.gal/bopportal/2026_0000003193.html
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

No `data/html_monitor/` output directory was created by the preview because `--write` was not used.

## MCP Coverage

The MCP coverage surface remains read-only and can expose:

- `list_sources`
- `get_source_status`
- `list_monitorable_sources`
- `list_latest_discovery_entries`

`list_monitorable_sources` now includes `BOP_A_CORUNA` as a monitorable HTML source.

`list_latest_discovery_entries` still reads existing RSS/API JSONL only. Reading existing HTML
monitor JSONL from MCP remains a separate possible task:

```text
TASK-MCP-HTML-DISCOVERY-OUTPUT-001
```

## Safety Boundaries

Confirmed:

- HTML discovery is metadata-only;
- RSS/API discovery remains metadata-only;
- MCP coverage is read-only;
- `inventory_only` entries are not monitored;
- no automatic `source_candidates`;
- no automatic evidence-grade promotion;
- no PDF/artifact download;
- no downstream writes;
- no broad/all-source monitor runs;
- `--write` remains required for JSONL output.

## Coverage v1.4 Assessment

The platform now has:

- an executable registry with 65 official source entries;
- 6 RSS/Atom metadata-only discovery sources;
- 1 API metadata-only discovery source;
- 1 HTML provincial metadata-only discovery source;
- 42 remaining provincial inventory-only sources;
- read-only MCP coverage tools;
- no downstream/product coupling from registry or discovery work.

This is the first snapshot where the platform has coverage across three discovery families:

```text
RSS/Atom -> API -> HTML provincial
```

The HTML provincial path is intentionally narrow. It validates the pattern for one source, not a
bulk provincial monitoring strategy.

## Next Recommended Tasks

Recommended next task:

```text
TASK-MCP-HTML-DISCOVERY-OUTPUT-001
```

Boundary:

- read existing `data/html_monitor/<source>/<date>/html_discovery.jsonl` only;
- do not fetch live HTML from MCP;
- do not write files from MCP;
- keep candidate/evidence statuses unchanged.

Alternative:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-002
```

Only after choosing at most 1-2 additional provincial sources with verified, simple official access
paths. Do not bulk-monitor provincial sources.

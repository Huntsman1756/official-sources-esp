# Source coverage v1.6 snapshot - 2026-05-29

Task: `TASK-SOURCE-COVERAGE-V1.6-SNAPSHOT-001`

## Scope

This is a reporting/control-plane snapshot after `TASK-SOURCE-RSS-MONITOR-005`.

Current integrated commit:

```text
97c05e7 feat(rss): add monitor 005 feeds
```

Source of truth:

```text
config/sources.yaml
```

This report does not add sources, ingestion behavior, candidates, evidence, artifacts, backfills,
RSS/API/HTML writes, downstream writes, VPS operations, production DB operations, Hermes operations,
systemd changes, or LLM classification.

## Registry Totals

Total registered executable sources: 65.

Counts by `jurisdiction_level`:

| jurisdiction_level | count |
| --- | ---: |
| `autonómica` | 19 |
| `estatal` | 2 |
| `european` | 1 |
| `provincial` | 43 |

Counts by `operational_status`:

| operational_status | count |
| --- | ---: |
| `inventory_only` | 41 |
| `metadata_adapter_validated` | 9 |
| `monitor_validated` | 15 |

Counts by `monitor_support`:

| monitor_support | count |
| --- | ---: |
| `available` | 24 |
| `none` | 41 |

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
| `BOE` | `rss` | State/control source. |
| `BOJA` | `atom` | Complete BOJA web feed. |
| `BOIB` | `rss` | Official BOIB feed. |
| `BOC_CANARIAS` | `rss` | Section-scoped to `I. Disposiciones generales`; not complete bulletin coverage. |
| `BOC_CANTABRIA` | `rss` | Official category feed; not complete bulletin coverage. |
| `BOCM` | `rss` | Official BOCM summary feed added by RSS-005; broader BOCM HTML/XML work remains paused. |
| `BOCYL` | `rss` | First autonomous bulletin RSS pilot. |
| `BOP_BADAJOZ` | `atom` | Official BOP Badajoz Atom feed added by RSS-005; uses Atom `updated` when `published` is absent. |
| `BOP_LUGO` | `rss` | Official BOP Lugo feed; PDF links may appear as metadata only. |
| `DOE` | `rss` | Official DOE feed; RSS-003 preview previously returned zero records. |
| `DOG` | `rss` | Complete DOG summary RSS feed. |

API metadata-only discovery monitor source:

| source_code | endpoint |
| --- | --- |
| `BOPV` | `https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}` |

HTML provincial metadata-only discovery sources:

| source_code | endpoint | status note |
| --- | --- | --- |
| `BOP_A_CORUNA` | `https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}` | Healthy in last combined provincial health check. |
| `BOP_ALBACETE` | `https://bop.dipualba.es` | Healthy in last combined provincial health check. |
| `BOP_ALICANTE` | `https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php` | Degraded/manual-review due resolver-dependent DNS instability. |
| `BOP_BARCELONA` | `https://bop.diba.cat/butlleti-del-dia` | Healthy in last combined provincial health check. |
| `BOP_BIZKAIA` | `https://www.bizkaia.eus/es/bob` | Healthy in last combined provincial health check. |
| `BOP_MALAGA` | `http://www.bopmalaga.es/` | Healthy in last combined provincial health check. |
| `BOP_VALENCIA` | `https://bop.dival.es/bop/drvisapi.dll` | Healthy in last combined provincial health check. |

Current discovery-family summary:

```text
RSS/Atom discovery: 11 sources
API discovery: 1 source
HTML provincial discovery: 7 sources
provincial inventory-only sources: 34
```

## RSS-005 Summary

`TASK-SOURCE-RSS-MONITOR-005` selected:

```text
BOCM
BOP_BADAJOZ
```

Live preview results from RSS-005:

```text
BOCM: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOP_BADAJOZ: records=1 feed_format=atom candidate_status=not_candidate evidence_status=not_evidence
data/rss_monitor exists: false
```

RSS-005 did not touch VPS, Hermes, timers, systemd, candidates, evidence-grade records, artifacts,
downstream repositories, or persistent monitor output.

## Health And Risk Notes

Known operationally healthy from the latest combined provincial health contract:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_LUGO
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
```

Known degraded/manual-review:

```text
BOP_ALICANTE
reason: resolver-dependent DNS instability for sede.diputacionalicante.es
```

Recently validated by RSS-005 preview:

```text
BOCM
BOP_BADAJOZ
```

No all-sources-green claim is made by this snapshot.

## MCP Coverage

The MCP coverage surface can expose:

- `list_sources`
- `get_source_status`
- `list_monitorable_sources`
- `list_latest_discovery_entries`
- `preview_discovery`
- `recommend_next_sources`

Current read-only MCP monitorable-source count:

```text
23
```

`list_latest_discovery_entries` reads existing RSS/API/HTML JSONL only. It does not fetch live
sources and does not write files.

`preview_discovery` may run a controlled one-source preview for validated RSS/API/HTML sources, but
it does not write JSONL or mutate state.

`recommend_next_sources` is deterministic, does not fetch live sources, does not run previews, and
does not write files. After RSS-005, `BOP_BADAJOZ` is no longer a provincial `inventory_only`
recommendation. The current top recommendations are:

```text
BOP_SEVILLA
BOP_ZARAGOZA
BOP_ARABA_ALAVA
BOP_AVILA
BOP_BURGOS
BOP_CACERES
BOP_CADIZ
BOP_CASTELLON
```

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
- no Hermes or systemd operations;
- no LLM classification.

## Coverage v1.6 Assessment

The platform now has:

- an executable registry with 65 official source entries;
- 11 RSS/Atom metadata-only discovery sources;
- 1 API metadata-only discovery monitor source;
- 7 HTML provincial metadata-only discovery sources;
- 34 remaining provincial inventory-only sources;
- read-only MCP coverage and cache-readback tools;
- controlled MCP one-source previews;
- deterministic MCP next-source recommendations;
- no downstream/product coupling from registry or discovery work.

RSS-005 closes the pending feed-selection item without expanding candidate/evidence behavior.
`BOP_ALICANTE` remains the main known degraded monitored source and must stay excluded from
all-sources-green claims until normal DNS/live preview recovers.

## Next Recommended Task

Recommended next task:

```text
TASK-PROVINCIAL-MONITORS-WAVE-003
```

Boundary:

- proceed only under the existing partial-health contract;
- keep `BOP_ALICANTE` degraded/manual-review and excluded from healthy-set claims;
- evaluate at most the next small provincial monitor wave;
- preview first;
- no JSONL writes unless explicitly authorized;
- no candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS/prod DB,
  Hermes, systemd, or LLM classification.

## Validation

Read-only snapshot inputs:

```text
git rev-parse --short HEAD: 97c05e7
python registry count script from config/sources.yaml
python MCP read-only list_monitorable_sources/recommend_next_sources checks
python provincial audit inventory count check
```

Final validation:

```text
python -m pytest tests/test_source_registry.py tests/test_mcp_tools.py tests/test_provincial_readonly_audit.py -q: 53 passed, 1 warning
python -m ruff check src tests: OK
git diff --check: OK
```

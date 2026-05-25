# Source coverage v1.3 snapshot - 2026-05-24

Task: `TASK-SOURCE-COVERAGE-V1.3-SNAPSHOT-001`

Run date: 2026-05-25

## Scope

This is a reporting/control-plane snapshot after `TASK-SOURCE-OFFICIAL-DIRECTORY-001`.

Current integrated commit:

```text
c5f8733 docs/config: reconcile source registry with official directories
```

Source of truth:

```text
config/sources.yaml
```

This report does not add sources, ingestion behavior, candidates, evidence, artifacts, backfills,
RSS/API writes, downstream writes, VPS operations, production DB operations, or LLM classification.

## Registry Totals

Total registered executable sources:

```text
before official directory reconciliation: 22
after official directory reconciliation: 65
```

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
| `inventory_only` | 52 |
| `metadata_adapter_validated` | 9 |
| `monitor_validated` | 3 |
| `paused` | 1 |

Counts by `monitor_support`:

| monitor_support | count |
| --- | ---: |
| `available` | 12 |
| `none` | 52 |
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

## Official Directory Reconciliation

Reviewed official directory pages:

- BOE "Otros diarios oficiales": `https://www.boe.es/legislacion/otros_diarios_oficiales.php`
- PAG general "Boletines Oficiales": `https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/boletinesOficiales.html`
- PAG CCAA "Boletines oficiales de las Comunidades Autonomas": `https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/BO_CCAA.html`
- PAG diputaciones "Boletines oficiales de las Diputaciones Provinciales": `https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/BO_Diputaciones.html`

The reconciliation added 43 provincial bulletin sources as `inventory_only` entries. These are
canonical inventory records only. Their `html` access methods are directory landing URLs with
`status=inventory`; they are not validated HTML monitors.

PAG diputaciones states that provinces belonging to uniprovincial autonomous communities and
Ceuta/Melilla do not have separate provincial bulletins. No provincial registry entry was added for
those cases.

## Current Monitored Sources

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

Provincial sources are not currently monitored.

## MCP Coverage

The MCP coverage surface remains read-only and can expose:

- `list_sources`
- `get_source_status`
- `list_monitorable_sources`
- `list_latest_discovery_entries`

`list_latest_discovery_entries` reads existing RSS/API JSONL only. It does not fetch live sources
and does not write output.

## Safety Boundaries

Confirmed:

- `inventory_only` is not monitored;
- RSS/API discovery is metadata-only;
- MCP coverage is read-only;
- no automatic `source_candidates`;
- no automatic evidence-grade promotion;
- no PDF/artifact download;
- no downstream writes;
- no broad/all-source monitor runs;
- `--write` remains required for RSS/API JSONL output.

## Coverage v1.3 Assessment

The platform now has:

- an executable registry with 65 official source entries;
- complete autonomous/statutory-city bulletin inventory from BOE/PAG directory coverage;
- 43 provincial bulletin entries represented as inventory-only;
- 6 RSS/Atom metadata-only discovery sources;
- 1 API metadata-only discovery source;
- read-only MCP coverage tools;
- no downstream/product coupling from registry or discovery work.

The registry is now a broader canonical map, but most provincial entries remain unobserved. This is
intentional: inventory completeness is not the same as monitor validation.

## Next Recommended Tasks

Recommended next task:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001
```

Boundary:

- choose one provincial source only;
- verify its official access path before implementation;
- keep output metadata-only;
- no bulk provincial monitoring;
- no PDFs/artifacts;
- no candidates;
- no evidence-grade promotion;
- no downstream writes.

Other possible follow-up:

```text
TASK-SOURCE-PROVINCIAL-URL-DIFF-AUDIT-001
```

Use this if the next step is to compare BOE/PAG provincial URL differences before any provincial
monitor pilot.

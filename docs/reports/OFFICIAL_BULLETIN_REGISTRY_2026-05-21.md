# Official Bulletin Registry Import

Task: `TASK-SOURCES-REGISTRY-001 - BOE official bulletin registry import`

Report file date: 2026-05-21.
Source index rechecked: 2026-05-22.

## Objective

Create a canonical static registry of official bulletin sources for `official-sources` using the
BOE "Otros diarios oficiales" page as the starting official index.

Source index:

- <https://www.boe.es/legislacion/otros_diarios_oficiales.php>

## Scope

This was registry/documentation work only.

No adapters were implemented. No backfills were run. No candidates were created. No PDFs were
downloaded. No downstream projects were touched.

## Output

Created:

- `docs/OFFICIAL_BULLETIN_REGISTRY.md`

The registry includes the required columns:

```text
source_code
official_name
level
jurisdiction
territory
official_url
boe_index_label
current_status
adapter_priority
notes
```

## Coverage Counts

| coverage group | count |
| --- | ---: |
| State project source | 1 |
| European source from BOE index | 1 |
| Autonomous/statutory territory sources from BOE index | 19 |
| Provincial sources from BOE index | 43 |

The autonomous/statutory count includes the 17 autonomous/community-level sources plus BOCCE and
BOME for Ceuta and Melilla.

## Initial Status Assignment

| source_code | status | reason |
| --- | --- | --- |
| BOE | `implemented` | Existing Tier 1 source in this project. |
| BOJA | `pilot_validated` | BOJA metadata adapter and controlled pilot have been validated. |
| BOCM | `mvp_implemented_paused` | Metadata MVP exists, but broader work is paused on observed connectivity/endpoint instability. |
| DOGV | `audited_p1` | DOGV audit found direct official JSON by date and recommends a metadata adapter MVP. |
| All other BOE-indexed sources | `not_audited` | Listed by the BOE index but not yet audited for adapter feasibility. |

## Recommended Next Source Work

1. `TASK-AUTO-DOGV-002 - DOGV metadata adapter MVP`.
   DOGV should be next because the audit found direct official JSON by date.
2. BOCM retry later.
   Keep BOCM paused until the connectivity/endpoint instability can be retried cleanly.
3. Provincial bulletins after one more autonomous source is stable.
   The BOE page is a good coverage inventory, but BOPs are heterogeneous and need individual
   source audits before adapter work.

## Files Changed

- `docs/OFFICIAL_BULLETIN_REGISTRY.md`
- `docs/reports/OFFICIAL_BULLETIN_REGISTRY_2026-05-21.md`
- `docs/ROADMAP.md`

## Validation

Run before commit:

```text
git diff --check
```

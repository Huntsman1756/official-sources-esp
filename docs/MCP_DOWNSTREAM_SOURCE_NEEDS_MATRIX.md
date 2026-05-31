# MCP Downstream Source Needs Matrix

Date: 2026-05-31

Task: `TASK-MCP-DOWNSTREAM-SOURCE-NEEDS-MATRIX-001`

This document defines how `official-sources` should evolve as a shared read-only MCP/upstream for
current and future downstream projects.

It replaces source expansion by intuition with source expansion by downstream demand.

## Current Baseline

```text
registered sources: 65
metadata_adapter_validated: 9
monitor_validated: 15
inventory_only: 41
monitor_support=available: 24
evidence_adapter=true: 6
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
BOP_ALICANTE runtime health: degraded/manual-review
writes: disabled
```

Source status semantics are defined in:

```text
docs/SOURCE_STATUS_CONTRACT.md
```

The registry is not a product-readiness list. Registry presence, monitor support, monitor
validation, or runtime health must not be interpreted as permission to create candidates, create
evidence-grade records, write downstream data, or publish product content.

## MCP Direction

`official-sources` should be the shared official-source layer for:

```text
G:\_Proyectos\oposiciones2.0\
G:\_Proyectos\eduayudas\
G:\_Proyectos\la-ayuda\
G:\_Proyectos\renta-verificable\
future MCP consumers
```

It should provide read-only official-source capability:

```text
source registry
source status and runtime-health interpretation
metadata-only discovery
official identifiers and URLs
citations and integrity metadata
reviewable evidence packets
normative reference resolution
source recommendations by downstream demand
```

It must not provide:

```text
downstream writes
publication decisions
candidate approval
evidence-grade promotion without an explicit adapter and task
eligibility decisions
tax conclusions
product ranking
notifications
public pages
```

## Demand Classes

Downstream needs should be grouped by use case, not only by source administration.

| Demand class | Primary consumers | Required MCP capability | Main safety boundary |
| --- | --- | --- | --- |
| `public_employment_alerts` | `oposiciones2.0` | metadata discovery, alert-grade export, official URL, dedupe key | metadata is not evidence-grade and must stay reviewable |
| `education_aid_evidence` | `eduayudas` | reviewed evidence packet, citation, integrity, source URL | evidence staging is not aid creation or publication |
| `benefit_source_discovery` | `la-ayuda` | official source discovery, normative reference, evidence packet | source match is not benefit-page approval |
| `fiscal_reference_resolution` | `renta-verificable` | AEAT/BOE/autonomous legal reference resolution | source reference is not fiscal advice |
| `future_grants_registry` | future grants/subsidy products | BDNS convocatoria metadata, identifiers, hashes, controlled exports | BDNS data is not automatic product publication |

## Downstream Matrix

| Project | Product need | Current consumer state | Useful current source families | Missing source families or capability | MCP priority | Next MCP task |
| --- | --- | --- | --- | --- | --- | --- |
| `oposiciones2.0` | Official public-employment alerts from BOE, autonomous bulletins, and BOPs. | MVP closed-beta hardening; BOE, DOGV, BOP Castellon, BOP Valencia, and partial BOP Alicante are already product-side concepts. | BOE, DOGV, BOCM/BOJA as registry/monitor candidates, selected provincial monitors, alert-grade exports. `BOP_CASTELLON` and `BOP_SEVILLA` now have shared metadata-only monitors. | More provincial BOP metadata monitors with employment relevance; `BOP_ALICANTE` remains degraded/manual-review. | High | Continue with low-friction public-employment BOP sources only after explicit task. |
| `eduayudas` | Verified education-aid evidence with official URL and verification date. | Evidence staging, preview, explicit evidence writes, explicit candidate conversion, and explicit draft pilot exist product-side. | BOE, BOJA, BOCYL, BOCM, DOGV, BDNS, autonomous bulletins. | Fresh reviewable evidence packets for education-aid searches; BDNS/education portal prioritization; product-scoped evidence exports, not global candidate creation. | High | `TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001` |
| `la-ayuda` | Official source discovery and evidence for benefits/prestations catalog cards. | Static catalog; staging-first official-sources integration exists; many cards still require review or exact normative source discovery. | BOE, consolidated law tools, autonomous bulletins, selected evidence exports. | Normative source resolver for pending cards; official portal/sede source discovery; autonomous social-services, housing, family, dependency, disability, and benefit sources. | High | `TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001` |
| `renta-verificable` | Exact fiscal/legal references for IRPF deductions. | Pre-beta local release candidate; production remains NO-GO pending infrastructure; fiscal/legal data is protected from casual edits. | BOE consolidated law tools, future autonomous legal reference support; AEAT remains primary outside current registry. | AEAT manual/reference source support; exact BOE/autonomous legal references; audit of generated or generic BOE links before integration. | Medium | `TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001` |
| future grants/subsidy products | Grants and subsidy discovery. | No named current product dependency in this task. | BDNS convocatorias adapter family, BOE/autonomous evidence. | Grants-specific staging model; concessions privacy/retention review before use. | Medium | `TASK-MCP-BDNS-GRANTS-DEMAND-001` |

## Source Expansion Priority

Do not reopen all `inventory_only` sources.

Reopen source coverage only when at least one downstream demand class names a concrete use case and
the source can be kept read-only.

### First Wave: Public Employment Alerts

Primary consumer:

```text
oposiciones2.0
```

Recommended first-wave source work:

| Source | Why it matters | Current planning signal | Required output |
| --- | --- | --- | --- |
| `BOP_CASTELLON` | Already useful in `oposiciones2.0`; reconciled into shared MCP coverage. | Provincial audit classified it as `stable_form_or_endpoint`, candidate `yes`. | metadata-only HTML monitor implemented |
| `BOP_SEVILLA` | High-value provincial employment source and previous recommended candidate. | Provincial audit classified it as `stable_form_or_endpoint`, candidate `yes`. | metadata-only HTML monitor implemented |
| `BOP_AVILA` | Low-friction provincial feed/API signal. | `rss_or_api_detected`, candidate `yes`. | metadata-only RSS/API or preview task |
| `BOP_PONTEVEDRA` | Low-friction provincial feed/API signal. | `rss_or_api_detected`, candidate `yes`. | metadata-only RSS/API or preview task |
| `BOP_SORIA` | Low-friction provincial feed/API signal. | `rss_or_api_detected`, candidate `yes`. | metadata-only RSS/API or preview task |
| `BOP_CORDOBA` | Open-data signal and public-employment relevance. | `open_data_detected`, candidate `yes`. | metadata-only monitor or preview task |
| `BOP_GRANADA` | Open-data signal and public-employment relevance. | `open_data_detected`, candidate `yes`. | metadata-only monitor or preview task |
| `BOP_LEON` | Open-data signal and public-employment relevance. | `open_data_detected`, candidate `yes`. | metadata-only monitor or preview task |
| `BOP_PALENCIA` | Open-data signal and public-employment relevance. | `open_data_detected`, candidate `yes`. | metadata-only monitor or preview task |
| `BOP_SALAMANCA` | Open-data signal and public-employment relevance. | `open_data_detected`, candidate `yes`. | metadata-only monitor or preview task |

Rules for this wave:

- metadata-only;
- one source at a time or very small waves;
- no candidate creation;
- no evidence-grade records;
- no PDF/artifact downloads by default;
- no downstream writes;
- no claim that all monitored provincial sources are green while `BOP_ALICANTE` remains
  `degraded/manual-review`.

### Second Wave: Education Aid And Benefit Evidence

Primary consumers:

```text
eduayudas
la-ayuda
```

Recommended capability work:

| Capability | Why it matters | Required output |
| --- | --- | --- |
| BDNS education-aid profile | Grants and scholarships often appear in BDNS before or alongside product-specific publication. | reviewable evidence packet/export, not automatic aid creation |
| Autonomous bulletin scoped searches | Education and social aids are frequently autonomous. | source-specific search/export profiles |
| Official portal/sede source discovery | Many benefit pages are not best represented by daily bulletin monitors. | resolver output with URL, source type, confidence, and manual-review flag |
| Evidence packet profile per consumer | `eduayudas` and `la-ayuda` have different staging models. | consumer-scoped JSON examples and validation contract |

### Third Wave: Fiscal Reference Resolution

Primary consumer:

```text
renta-verificable
```

Recommended capability work:

| Capability | Why it matters | Required output |
| --- | --- | --- |
| AEAT-first reference model | AEAT remains primary for IRPF guidance. | source policy and resolver contract |
| BOE/autonomous legal reference audit | Generic BOE links or generated-looking references are unsafe for fiscal claims. | exact official identifier, URL, reviewed date, uncertainty state |
| Autonomous tax-source inventory | Fiscal rules may depend on CCAA, foral systems, Ceuta, and Melilla. | inventory plus explicit gaps |

This wave should start only after `renta-verificable` completes its production infrastructure gate
or explicitly requests a source audit before launch.

## MCP Capability Backlog

The MCP layer should grow in this order:

| Capability | Status | Notes |
| --- | --- | --- |
| `list_sources` | implemented | Registry read-only. |
| `get_source_status` | implemented | Source-specific status and safety flags. |
| `list_monitorable_sources` | implemented | Registry-declared monitorable sources only. |
| `list_latest_discovery_entries` | implemented | Reads existing JSONL only. |
| `preview_discovery` | implemented | One explicit source, small limit, no writes. |
| `recommend_next_sources` | implemented | Registry/cache recommendation, not downstream-demand aware yet. |
| `recommend_sources_for_consumer` | proposed | Should use this matrix to rank work by consumer demand. |
| `discover_sources_for_case` | proposed | Should return source candidates for a product use case without fetching arbitrary URLs. |
| `build_evidence_packet` | proposed | Should produce reviewable evidence envelopes only for supported source families. |
| `resolve_normative_reference` | proposed | Should resolve exact official references without legal interpretation. |
| `resolve_fiscal_reference` | proposed | Should be AEAT-first and fiscal-review gated. |

## Acceptance Gates For New Source Work

A future source expansion task must state:

- downstream demand class;
- consumer project(s);
- source code(s);
- current registry state;
- intended capability (`metadata-only`, `evidence packet`, or `reference resolver`);
- command scope;
- write policy;
- candidate/evidence policy;
- validation commands;
- manual-review criteria;
- rollback or supersede path.

No source expansion task may weaken these current rules:

```text
candidate_creation_allowed=false for all sources unless a future explicit source-specific task changes it
evidence_grade_allowed=false for all sources unless a future explicit source-specific task changes it
official-sources remains read-only toward downstream repositories
BOP_ALICANTE remains degraded/manual-review until a separate recovery task proves otherwise
```

## Immediate Next Tasks

```text
TASK-MCP-OFFICIAL-SOURCES-CONTRACT-001
TASK-MCP-CASE-TAXONOMY-001
TASK-MCP-TOOLS-READONLY-SKELETON-001
TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001
TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001
TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001
TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001
```

Recommended order:

1. Define the MCP downstream-demand contract and case taxonomy.
2. Add read-only MCP outputs that expose consumer-aware recommendations.
3. Reopen only the public-employment source wave needed by `oposiciones2.0`.
4. Add evidence-packet and source-resolver flows for `eduayudas` and `la-ayuda`.
5. Add fiscal reference resolution only after the `renta-verificable` infrastructure gate or a
   product-specific source audit request.

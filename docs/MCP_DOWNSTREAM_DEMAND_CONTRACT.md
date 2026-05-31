# MCP Downstream Demand Contract

Date: 2026-05-31

Task: `TASK-MCP-OFFICIAL-SOURCES-CONTRACT-001`

This contract defines the downstream-demand MCP surface that should sit on top of the existing
source registry, source status contract, and read-only MCP tools.

It is a specification contract. It does not implement new MCP tools, add sources, fetch live data,
write monitor output, create candidates, create evidence-grade records, write downstream data, or
change runtime behavior.

Related contracts:

```text
docs/SOURCE_STATUS_CONTRACT.md
docs/DOWNSTREAM_CONTRACT.md
docs/MCP_CASE_TAXONOMY.md
docs/MCP_DOWNSTREAM_SOURCE_NEEDS_MATRIX.md
docs/MCP_TOOLS.md
```

## Contract Goal

The MCP should help downstream consumers answer:

```text
Which official sources are relevant to this product use case?
What is each source capable of today?
What may the consumer safely infer?
What must still be reviewed by the product?
What source work should be prioritized next?
```

The MCP must not turn relevance into approval.

## Consumer Model

Stable demand classes, case types, topic values, jurisdiction values, safe outputs, and
`must_not_infer` values are defined in:

```text
docs/MCP_CASE_TAXONOMY.md
```

Supported current consumers:

| Consumer | Demand class | MCP role |
| --- | --- | --- |
| `oposiciones2.0` | `public_employment_alerts` | metadata discovery and alert-grade planning |
| `eduayudas` | `education_aid_evidence` | reviewable evidence-packet planning |
| `la-ayuda` | `benefit_source_discovery` | official source discovery and normative-reference planning |
| `renta-verificable` | `fiscal_reference_resolution` | exact fiscal/legal reference planning |

Future consumers must be onboarded through an explicit profile before receiving consumer-specific
recommendations.

## Shared Response Envelope

Every downstream-demand tool should return an envelope with these fields:

```json
{
  "status": "ok|cache_miss|not_supported|manual_review_required|refused",
  "consumer": "oposiciones2.0",
  "demand_class": "public_employment_alerts",
  "mode": "read_only",
  "writes_performed": false,
  "candidate_creation_allowed": false,
  "evidence_grade_allowed": false,
  "product_automation_allowed": false,
  "human_review_required": true,
  "contract_refs": [
    "docs/SOURCE_STATUS_CONTRACT.md",
    "docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md"
  ],
  "items": []
}
```

No downstream-demand tool may omit the safety fields when returning source recommendations,
evidence-packet candidates, or reference-resolution candidates.

## Source Status Object

Whenever a tool returns a source, it should include:

```json
{
  "source_code": "BOP_SEVILLA",
  "registered": true,
  "registry_operational_status": "inventory_only",
  "runtime_health": "unknown|healthy|degraded/manual-review",
  "monitor_support": "none|available",
  "evidence_adapter": false,
  "candidate_creation_allowed": false,
  "evidence_grade_allowed": false,
  "product_ready": false,
  "safe_downstream_uses": [
    "inventory_awareness",
    "manual_review"
  ],
  "must_not_infer": [
    "candidate_ready",
    "evidence_grade",
    "publication_ready"
  ]
}
```

`runtime_health` must be represented as a separate field from `registry_operational_status`.

`BOP_ALICANTE` must be returned as `degraded/manual-review` until a later recovery task documents
normal runtime recovery.

## Tool Contracts

The following tools define the downstream-demand MCP surface. Implementation status is tracked in
`docs/MCP_TOOLS.md`.

### `list_case_taxonomy`

Status:

```text
implemented
```

Purpose:

```text
Expose stable downstream case types, demand classes, source-family targets, and safety boundaries.
```

Inputs:

```json
{
  "consumer": "optional known consumer or alias",
  "demand_class": "optional demand-class filter"
}
```

Required behavior:

- return deterministic taxonomy entries from `docs/MCP_CASE_TAXONOMY.md`;
- preserve the shared safety envelope;
- refuse unknown consumers;
- refuse unsupported demand classes;
- refuse consumer/demand-class mismatches.

Must not:

- fetch live sources;
- run discovery previews;
- write JSONL;
- mutate `config/sources.yaml`;
- create candidates or evidence-grade records;
- write downstream records;
- decide eligibility, legal meaning, fiscal meaning, product ranking, or publication readiness.

### `recommend_sources_for_consumer`

Status:

```text
implemented
```

Purpose:

```text
Rank source work by known downstream demand instead of generic registry completion.
```

Inputs:

```json
{
  "consumer": "oposiciones2.0|eduayudas|la-ayuda|renta-verificable",
  "demand_class": "optional demand class override",
  "limit": 5
}
```

Required behavior:

- read only from registry, documented reports, and explicit planning metadata;
- return source recommendations with source status objects;
- include why each source matters to the consumer;
- include required next task type;
- refuse unknown consumers unless a profile exists;
- refuse broad automatic expansion requests.

Must not:

- fetch live sources;
- run previews;
- write JSONL;
- mutate `config/sources.yaml`;
- create candidates or evidence-grade records;
- write downstream records.

### `discover_sources_for_case`

Status:

```text
proposed
```

Purpose:

```text
Given a product case, return relevant official-source families and gaps.
```

Inputs:

```json
{
  "consumer": "la-ayuda",
  "case_type": "benefit_source_discovery",
  "jurisdiction": "state|autonomous|provincial|local|foral|ceuta_melilla",
  "topic": "housing|education|family|dependency|disability|public_employment|tax",
  "limit": 10
}
```

Required behavior:

- return source families and candidate official sources;
- distinguish registered sources from missing source families;
- flag `inventory_only` sources as planning-only;
- return manual-review requirements;
- avoid arbitrary URL fetching.

Must not:

- invent source URLs;
- treat a source family as verified evidence;
- decide eligibility, amount, deadline, or legal meaning.

### `build_evidence_packet`

Status:

```text
implemented for eduayudas education-aid profiles
```

Purpose:

```text
Prepare reviewable evidence metadata for supported sources and consumers.
```

Inputs:

```json
{
  "consumer": "eduayudas",
  "source_code": "BDNS|BOE|BOJA|BOCYL|BOCM|DOGV",
  "official_identifier": "optional review target",
  "profile": "education_aid"
}
```

Required behavior:

- return a review-only packet profile and required packet fields;
- distinguish source requirements from existing evidence;
- identify missing source families such as education portals;
- preserve the shared read-only safety envelope;
- mark output as staging/review only;
- return unsupported consumers, profiles, and sources as structured refusals.

Must not:

- download missing artifacts unless a separate explicit artifact task authorizes it;
- create product candidates;
- approve or publish benefits/aids;
- mark output evidence-grade unless the source-specific evidence contract allows it.

### `resolve_normative_reference`

Status:

```text
implemented for la-ayuda source-lead planning
```

Purpose:

```text
Resolve exact official references for benefit/social-aid cards without legal interpretation.
```

Inputs:

```json
{
  "consumer": "la-ayuda",
  "topic": "benefits|housing|family|dependency|disability|social_services",
  "jurisdiction": "Comunidad de Madrid",
  "known_title": "optional current product title",
  "limit": 10
}
```

Required behavior:

- return possible official source families and registered sources;
- distinguish exact references from unresolved source leads;
- require manual review for unresolved or ambiguous matches;
- include uncertainty state;
- return `manual_review_required` while exact references are unresolved.

Must not:

- create Markdown content;
- rewrite product claims;
- decide benefit eligibility;
- cite generated or generic links as exact references.

### `resolve_fiscal_reference`

Status:

```text
implemented for renta-verificable source-lead planning
```

Purpose:

```text
Resolve AEAT-first and exact BOE/autonomous references for IRPF deduction records.
```

Inputs:

```json
{
  "consumer": "renta-verificable",
  "tax_year": 2025,
  "jurisdiction": "Madrid",
  "deduction_key": "optional product key",
  "limit": 10
}
```

Required behavior:

- treat AEAT as the primary fiscal guidance source;
- use BOE/autonomous references only as exact legal references;
- flag generic BOE home links as insufficient;
- require fiscal/legal product review before use;
- return `manual_review_required` while exact references are unresolved.

Must not:

- generate tax conclusions;
- update fiscal datasets;
- replace product-side legal review;
- claim a reference is current without an explicit reviewed date.

## Refusal Rules

Downstream-demand tools must refuse or return `manual_review_required` when:

- the consumer is unknown;
- the demand class is unsupported;
- the request asks for writes or publication;
- the request asks for all-source automation;
- the request asks for legal, fiscal, eligibility, ranking, or approval conclusions;
- the source is `inventory_only` and the requested capability requires a monitor;
- the source is `degraded/manual-review` and the request assumes operational green status.

## Versioning

This contract is additive by default.

Breaking changes require:

- a new task ID;
- an updated contract date;
- explicit migration notes;
- updates to `docs/MCP_TOOLS.md`;
- validation that existing consumers still receive safe refusal or safe cache-miss behavior.

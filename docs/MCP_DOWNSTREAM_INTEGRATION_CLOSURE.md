# MCP Downstream Integration Closure

Date: 2026-05-31

Task: `TASK-MCP-DOWNSTREAM-INTEGRATION-CLOSURE-001`

This contract closes the current downstream integration surface for:

- `oposiciones2.0`
- `eduayudas`
- `la-ayuda`
- `renta-verificable`

The closure is read-only upstream v1. It does not enable writes, product automation, candidate
creation, evidence-grade promotion, publication, live source expansion, or downstream repository
mutation.

Related contracts:

```text
docs/SOURCE_STATUS_CONTRACT.md
docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md
docs/MCP_DOWNSTREAM_SOURCE_NEEDS_MATRIX.md
docs/MCP_TOOLS.md
```

## Closure Boundary

`official-sources` is the upstream control plane for official-source discovery, source status,
source-family planning, and review-only evidence/reference profiles.

Downstream projects own:

- product records;
- imports;
- candidate staging;
- evidence review;
- legal/fiscal/editorial decisions;
- publication;
- user notifications.

No MCP tool may directly write to downstream projects.

## MCP Tool

The closure matrix is exposed by:

```text
list_downstream_integration_smokes
```

The closure checks are exposed by:

```text
check_downstream_integration_smokes
```

Inputs:

```json
{
  "consumer": "optional: oposiciones2.0|eduayudas|la-ayuda|renta-verificable|renta"
}
```

Every response preserves:

```text
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
```

The tool returns the smoke call each consumer should run against the current MCP surface, the
downstream preview command shape when one exists, required source families, required fields,
known risks, and explicit `must_not_do` constraints.

`check_downstream_integration_smokes` executes only hardcoded in-process `official-sources`
MCP/planner calls. It does not run downstream preview commands, shell commands, monitor previews,
live source fetches, JSONL writes, registry mutations, candidates, evidence-grade promotion, or
product writes.

## Consumer Smokes

### `oposiciones2.0`

Integration mode:

```text
json_export_preview_then_reviewed_import
```

MCP smoke call:

```json
{
  "tool": "recommend_sources_for_consumer",
  "arguments": {
    "consumer": "oposiciones2.0",
    "limit": 3
  }
}
```

Expected status:

```text
ok
```

Downstream preview shape:

```text
npm run import:strict-alerts:preview -- --file <strict_alerts.sample.jsonl>
```

Required boundary:

- strict alerts remain alert-grade, not evidence-grade;
- imports are previewed before product writes;
- no public-employment process, event, match, alert log, or notification is auto-created by MCP;
- `BOP_ALICANTE` recovered from its earlier DNS-dependent degradation on 2026-06-02; runtime
  all-green claims still require scoped runtime checks, not registry status alone.

### `eduayudas`

Integration mode:

```text
evidence_json_preview_then_private_staging
```

MCP smoke call:

```json
{
  "tool": "build_evidence_packet",
  "arguments": {
    "consumer": "eduayudas",
    "source_code": "BOE"
  }
}
```

Expected status:

```text
ok
```

Downstream preview shape:

```text
npm run official-sources:preview -- --file <evidence.json>
```

Required boundary:

- current downstream evidence import remains private staging;
- BOE evidence is usable only after integrity and product review gates;
- broader BDNS/autonomous education-aid source families require downstream schema review;
- MCP must not create `source_candidates` or `aid_programs`.

### `la-ayuda`

Integration mode:

```text
evidence_json_preview_then_pending_review_candidate
```

MCP smoke call:

```json
{
  "tool": "resolve_normative_reference",
  "arguments": {
    "consumer": "la-ayuda",
    "topic": "housing",
    "jurisdiction": "state",
    "limit": 3
  }
}
```

Expected status:

```text
manual_review_required
```

Downstream preview shape:

```text
npm run official-sources:preview -- --file <evidence.json>
```

Required boundary:

- source leads are not legal conclusions;
- staged candidates remain `pending_review`;
- no active Markdown benefit page is created automatically;
- no eligibility, amount, deadline, or publication decision is made by MCP.

### `renta-verificable`

Integration mode:

```text
build_time_reference_review_before_seed_import
```

MCP smoke call:

```json
{
  "tool": "resolve_fiscal_reference",
  "arguments": {
    "consumer": "renta-verificable",
    "tax_year": 2025,
    "jurisdiction": "Madrid",
    "deduction_key": "madrid-alquiler-vivienda-habitual-joven",
    "limit": 3
  }
}
```

Expected status:

```text
manual_review_required
```

Required boundary:

- AEAT is the first fiscal guidance source family;
- BOE/autonomous/foral sources are exact-reference leads only;
- MCP is not a fiscal source of truth;
- no deduction applicability, amount, entitlement, legal meaning, or verified product status is
  decided by MCP;
- the live app must not depend on MCP availability.

## Acceptance Gate

For all consumers, downstream product automation remains blocked until the product side completes
its own preview/import check and explicit review gate.

The upstream closure is acceptable when:

- `list_downstream_integration_smokes` returns one profile for each current consumer;
- `check_downstream_integration_smokes` returns a passing internal contract check for each current
  consumer;
- each profile contains the shared read-only safety envelope;
- each smoke points to an implemented MCP entrypoint or an explicit downstream preview contract;
- tests prove the smoke matrix does not write source candidates;
- no generated runtime data is created;
- `candidate_creation_allowed=false` remains true for all registered sources;
- `evidence_grade_allowed=false` remains true for all registered sources.

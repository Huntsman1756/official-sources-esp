# MCP Case Taxonomy

Date: 2026-05-31

Task: `TASK-MCP-CASE-TAXONOMY-001`

This contract defines the stable case taxonomy used by downstream-demand MCP tools.

The taxonomy exists so `official-sources` can feed current and future products through one shared
read-only MCP layer instead of hard-coding one-off source decisions inside each downstream project.

## Scope

The taxonomy defines:

- supported demand classes;
- supported case types;
- primary consumers;
- allowed topic and jurisdiction values;
- source-family planning targets;
- intended MCP capabilities;
- manual-review policy;
- safe outputs;
- facts consumers must not infer.

The taxonomy does not fetch live sources, run previews, write monitor output, create candidates,
create evidence-grade records, write downstream repositories, decide eligibility, decide legal or
fiscal meaning, publish pages, send notifications, or approve product automation.

## Shared Safety Envelope

Every taxonomy response must preserve:

```text
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
```

The taxonomy is a planning contract. It is not source evidence, product approval, eligibility
review, fiscal advice, legal advice, notification approval, or publication approval.

## Demand Classes

| Demand class | Case type | Primary consumer | Role |
| --- | --- | --- | --- |
| `public_employment_alerts` | `public_employment_alert` | `oposiciones2.0` | Metadata-only source discovery and alert-input planning. |
| `education_aid_evidence` | `education_aid` | `eduayudas` | Reviewable evidence-packet planning for education-aid records. |
| `benefit_source_discovery` | `benefit_source` | `la-ayuda` | Official source discovery and normative-reference planning for benefits. |
| `fiscal_reference_resolution` | `fiscal_reference` | `renta-verificable` | AEAT-first and exact official fiscal/legal reference planning. |
| `future_grants_registry` | `grant_registry` | future consumers | BDNS and grants/subsidy source-family planning. |

Future consumers must be added through an explicit taxonomy profile before receiving
consumer-specific recommendations or source-family planning.

## Supported Axes

Supported jurisdictions:

```text
state
autonomous
provincial
local
foral
ceuta_melilla
```

Supported topics:

```text
benefits
deductions
dependency
disability
education
family
grants
housing
irpf
public_employment
social_services
subsidies
tax
```

These values are classification inputs for MCP planning tools. They are not proof that a product
case is complete, publishable, legally correct, fiscally correct, or eligible.

## Case Contracts

### `public_employment_alerts`

Primary consumer:

```text
oposiciones2.0
```

Source families:

```text
BOE
autonomous_bulletins
provincial_bulletins
local_public_employment_surfaces
```

Safe outputs:

- source recommendation;
- metadata-only discovery record;
- official URL;
- manual-review alert input.

Must not infer:

- candidate-ready;
- evidence-grade;
- notification-ready;
- all sources green;
- product publication allowed.

`BOP_ALICANTE` remains `degraded/manual-review` and must not be used to claim that all monitored
provincial sources are green.

### `education_aid_evidence`

Primary consumer:

```text
eduayudas
```

Source families:

```text
BDNS
BOE
autonomous_bulletins
education_portals
```

Safe outputs:

- source recommendation;
- reviewable evidence-packet candidate;
- official URL;
- manual-review staging input.

Must not infer:

- aid created;
- aid published;
- eligibility decided;
- evidence-grade without adapter;
- product acceptance allowed.

Evidence staging is not aid creation, publication, eligibility review, or product acceptance.

### `benefit_source_discovery`

Primary consumer:

```text
la-ayuda
```

Source families:

```text
BOE
BDNS
autonomous_bulletins
official_portals
sede_electronica
```

Safe outputs:

- source recommendation;
- official source candidate;
- normative reference candidate;
- manual-review uncertainty state.

Must not infer:

- benefit page approved;
- eligibility decided;
- amount or deadline verified;
- publication-ready;
- legal meaning decided.

A source match is not benefit-page approval and is not a decision about eligibility, amount,
deadline, or legal meaning.

### `fiscal_reference_resolution`

Primary consumer:

```text
renta-verificable
```

Source families:

```text
AEAT
BOE
autonomous_bulletins
foral_tax_sources
```

Safe outputs:

- source recommendation;
- official reference candidate;
- review-date requirement;
- manual-review uncertainty state.

Must not infer:

- tax advice;
- deduction applicability decided;
- legal meaning decided;
- fiscal claim verified;
- product publication allowed.

Fiscal reference resolution must be AEAT-first where applicable. BOE, autonomous, foral, Ceuta, and
Melilla references must preserve exact identifiers, official URLs, reviewed dates, and uncertainty
states before downstream use.

### `future_grants_registry`

Primary consumer:

```text
future_grants_registry
```

Source families:

```text
BDNS
BOE
autonomous_bulletins
grant_portals
```

Safe outputs:

- source-family recommendation;
- convocatoria metadata planning;
- manual-review export input.

Must not infer:

- grant published;
- concession published;
- eligibility decided;
- privacy review completed;
- product publication allowed.

BDNS convocatoria metadata is not automatic product publication and must not be confused with
concession/award publication.

## MCP Tool

`list_case_taxonomy` exposes this taxonomy through MCP.

Inputs:

- `consumer`: optional known consumer alias such as `oposiciones2.0`, `eduayudas`, `la-ayuda`, or
  `renta-verificable`;
- `demand_class`: optional demand-class filter.

Required behavior:

- return deterministic taxonomy entries;
- preserve the shared safety envelope;
- refuse unknown consumers;
- refuse unsupported demand classes;
- refuse consumer/demand-class mismatches;
- avoid source fetches, monitor previews, JSONL writes, registry mutation, candidate creation,
  evidence-grade promotion, and downstream writes.

## Refusal Rules

The taxonomy must refuse or require manual review for:

- unknown consumers;
- unsupported demand classes;
- mismatched consumer and demand class;
- requests to write downstream data;
- requests to publish product content;
- requests to decide eligibility, legal meaning, fiscal meaning, or product ranking;
- broad all-source automation;
- any claim that `monitor_validated`, `monitor_support=available`, or registry presence means
  product readiness.

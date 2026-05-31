# MCP Renta-Verificable Fiscal Reference Profile

Date: 2026-05-31

Task: `TASK-MCP-FISCAL-REFERENCE-RESOLVER-RENTA-001`

This contract defines the first read-only fiscal reference planner for `renta-verificable`.

It returns source leads and manual-review requirements. It does not provide tax advice, decide
whether a deduction applies, verify a fiscal claim, interpret legal meaning, update product data,
fetch live sources, download artifacts, create candidates, create evidence-grade records, or write
to `G:\_Proyectos\renta-verificable\`.

## Source Policy

Fiscal references are AEAT-first where applicable.

| Source family | Role | Registry state |
| --- | --- | --- |
| `AEAT` | Primary fiscal guidance and practical manual source. | Not a registered source yet; returned as manual-review source family. |
| `BOE` | Exact state legal reference and consolidated-law source. | Registered source. |
| autonomous bulletins | Autonomous legal/reference source families. | Registered where present, such as `BOCM`, `DOGV`, `DOGC`, and `BOPV`. |
| foral tax sources | Foral reference source family. | Partially represented, such as `BON` and `BOPV`; semantics remain manual-review. |
| Ceuta/Melilla | Special fiscal-source territory. | Must be modeled explicitly before use. |

For Renta 2025, the planner may return AEAT manual URLs as source leads:

```text
https://sede.agenciatributaria.gob.es/Sede/Ayuda/25Manual/100.html
https://sede.agenciatributaria.gob.es/Sede/Ayuda/25Manual/100/deducciones-autonomicas.html
```

These URLs are source leads, not product-ready references.

## Output Semantics

Every `resolve_fiscal_reference` response must preserve:

```text
status=manual_review_required
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
exact_reference_resolved=false
```

The planner returns:

- source leads;
- source family;
- registry presence;
- official URL where already known;
- reviewed-date requirements;
- uncertainty state;
- manual-review reasons.

It does not return an exact reference until a later task can prove the official identifier, official
URL, version/review date, and uncertainty state.

## Supported Inputs

```json
{
  "consumer": "renta-verificable",
  "tax_year": 2025,
  "jurisdiction": "Madrid",
  "deduction_key": "optional product key",
  "limit": 10
}
```

Aliases:

```text
renta
renta-verificable
renta_verificable
```

## Must Not Infer

Consumers must not infer:

- tax advice;
- deduction applicability;
- legal meaning;
- fiscal claim verification;
- product publication allowed;
- exact current reference without reviewed date;
- evidence-grade status.

Manual review is required before any downstream dataset update, public UI copy, product claim,
deduction card, or user-facing tax reference.

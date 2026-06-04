# Downstream Integration Contracts

Date: 2026-06-04

Status: documentation-only contract.

This document defines how `official-sources` may serve downstream product repositories without
becoming product-specific infrastructure.

## Core Boundary

```text
official-sources = shared official-source registry, discovery, provenance, and review-only packets
downstream products = imports, staging, interpretation, review, publication, notifications, and UX
```

Adding more sources to `official-sources` increases shared upstream coverage. It does not, by
itself, feed any downstream product, create product records, or make data publishable.

Current upstream baseline:

```text
registered sources: 67
metadata_adapter_validated: 10
monitor_validated: 56
inventory_only: 1
remaining inventory_only source: DOUE
candidate_creation_allowed=false: 67/67
evidence_grade_allowed=false: 67/67
```

`check_downstream_integration_smokes` is a read-only contract smoke. It executes only hardcoded
in-process `official-sources` MCP/planner calls. It does not run downstream commands, execute
imports, fetch live sources, run monitor previews, write JSONL, mutate the registry, create
candidates, create evidence-grade records, or write product data.

## Non-Negotiable Invariants

- No MCP tool writes to downstream repositories.
- No MCP tool creates product records, candidates, evidence-grade records, notifications, or pages.
- No MCP tool decides legal meaning, fiscal meaning, eligibility, ranking, amount, deadline, or
  publication status.
- Every product integration must pass through a product-owned preview/import command and a human or
  editorial review gate.
- Source-family additions belong in `official-sources` only when the need is common or when a
  product-side acceptance smoke proves a concrete upstream gap.
- Product schemas, import code, staging records, review workflows, and publication workflows belong
  in the downstream repository.

## Product Matrix

| Project | Readiness | Allowed source families | Import mode | Review gate | Forbidden actions | Next task |
| --- | --- | --- | --- | --- | --- | --- |
| `eduayudas` | Best first pilot | BDNS, BOE, BOJA, BOCYL, BOCM, DOGV, and scoped education-aid official sources | Evidence JSON preview to private staging | Product review before aid candidate or draft use | Aid creation, eligibility decision, publication, notification, broad import | `TASK-EDUAYUDAS-OFFICIAL-SOURCES-REAL-PACKAGE-001` |
| `oposiciones2.0` | Partial; importer allowlist must be widened first | BOE, autonomous bulletins, selected BOPs needed by strict alerts | Strict-alert JSONL preview to reviewed staging import | Alert review before process/event/notification creation | Automatic process creation, evidence-grade promotion, notifications, allow-all source import | `TASK-OPOSICIONES-STRICT-ALERTS-ALLOWLIST-BOE-BOP-001` |
| `la-ayuda` | Cautious; source leads only | BOE, BDNS, BOCM, BOJA, DOGV, BOCYL, and product-specific official portals/sedes | Source lead or evidence preview to `pending_review` candidate | Human review before page publication | Autopublication, eligibility/amount/deadline conclusions, legal interpretation | `TASK-LAAYUDA-OFFICIAL-SOURCES-PENDING-REVIEW-PIPELINE-001` |
| `renta-verificable` | Not ready for product feed | AEAT first, then exact BOE/autonomous/foral reference leads | Reference audit only, no import | Fiscal/source review before any seed status change | Tax advice, deduction applicability, verified status, product dependency on MCP availability | `TASK-RENTA-AEAT-REFERENCE-AUDIT-001` |
| `subvenciones` | Use as shared provenance/cache, not replacement | BDNS and documented official grant-call context | Optional provenance/cache export beside the BDNS-native pipeline | Product review before replacing or enriching pipeline output | Replacing BDNS-native ingestion, global concession import, beneficiary publication | `TASK-SUBVENCIONES-BDNS-PROVENANCE-CACHE-CONTRACT-001` |
| `contratosabiertos` | PLACSP-specific contract required first | PLACSP, BOE procurement/legal context, later DOUE only after adapter work | PLACSP metadata/provenance export after gap audit | Procurement-domain review before product cases or flags | Risk conclusions, irregularity claims, review cases, transparency requests from MCP alone | `TASK-CONTRATOSABIERTOS-PLACSP-CONTRACT-GAP-AUDIT-001` |

## Operational Order

1. `eduayudas`: run a real, product-owned evidence package pilot.
2. `oposiciones2.0`: update the strict-alert source allowlist narrowly, starting with BOE and a
   small set of validated BOP/autonomous sources.
3. `la-ayuda`: keep the path source lead -> `pending_review` -> human review -> page.
4. `renta-verificable`: do not connect until the AEAT reference audit exists.
5. `subvenciones`: preserve the BDNS-native pipeline and use `official-sources` only for shared
   provenance/cache contracts.
6. `contratosabiertos`: define the PLACSP-specific gap contract before treating MCP output as
   product input, especially where minor-contract coverage matters.

## Interpretation

The MCP can be common infrastructure for all six projects only if each product keeps its own import
and review contract. It should not be adapted separately per project as a forked MCP, but each
downstream project still needs a narrow product-side integration layer.

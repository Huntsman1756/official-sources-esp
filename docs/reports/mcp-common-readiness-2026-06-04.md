# MCP Common Readiness Report

Date: 2026-06-04

Scope: documentation-only readiness assessment for using `official-sources` as a shared upstream MCP
for `oposiciones2.0`, `eduayudas`, `la-ayuda`, `renta-verificable`, `subvenciones`, and
`contratosabiertos`.

No imports, downstream writes, live monitor previews, registry mutations, source additions, or VPS
operations were performed for this report.

## Verdict

`official-sources` is useful as a common upstream source, provenance, and review-packet layer.

It is not yet a common product ingestion backend. Each downstream project still needs its own
preview/import contract, staging rules, and review gate. The MCP should not be forked or adapted per
project, but product-specific import and review code must remain in each product repository.

## Current Upstream Baseline

```text
registered sources: 67
metadata_adapter_validated: 10
monitor_validated: 56
inventory_only: 1
remaining inventory_only source: DOUE
candidate_creation_allowed=false: 67/67
evidence_grade_allowed=false: 67/67
```

The current MCP downstream smoke result is interpreted as a contract check only:

```text
status=ok
count=4
passed_count=4
failed_count=0
downstream_commands_executed=false
monitor_previews_executed=false
live_fetches_performed=false
jsonl_written=false
registry_mutated=false
```

This does not prove real downstream imports, product staging, publication readiness, runtime source
health, or product data correctness.

## Product Assessment

| Project | Current fit | Required before real integration |
| --- | --- | --- |
| `eduayudas` | Closest pilot candidate. Existing scripts indicate an official-sources preview/candidate/draft shape. | Run `TASK-EDUAYUDAS-OFFICIAL-SOURCES-REAL-PACKAGE-001` with a real evidence JSON package, private staging, migration/state confirmation, and review gate. |
| `oposiciones2.0` | Useful for alert-grade source recommendations, but current strict-alert import is source-limited. | Run `TASK-OPOSICIONES-STRICT-ALERTS-ALLOWLIST-BOE-BOP-001`; widen the importer allowlist narrowly instead of accepting every MCP source. |
| `la-ayuda` | Useful for official source leads and pending-review candidates. | Keep integration as source lead -> evidence preview -> `pending_review` -> human review -> page. No autopublication. |
| `renta-verificable` | Not ready for product feed because AEAT must remain the first fiscal source and there is no registered AEAT adapter in this MCP baseline. | Run `TASK-RENTA-AEAT-REFERENCE-AUDIT-001` before any import or verified-status change. |
| `subvenciones` | Should complement, not replace, the existing BDNS-native ingestion pipeline. | Define a BDNS provenance/cache export contract before connecting MCP output to product state. |
| `contratosabiertos` | Needs a PLACSP-specific contract. Current MCP PLACSP coverage is metadata-only and does not close product-specific contract/minor-contract gaps. | Run `TASK-CONTRATOSABIERTOS-PLACSP-CONTRACT-GAP-AUDIT-001` before any product case, risk flag, or publication workflow consumes MCP output. |

## Required Contract

The operative product contract is:

```text
docs/architecture/downstream-integration-contracts.md
```

It formalizes source-family scope, import mode, review requirements, forbidden actions, and first
next task per product.

## What Was Not Done

- No downstream repository was modified.
- No downstream command was executed.
- No product data was imported, staged, published, or deleted.
- No MCP source was added, removed, promoted, or live-previewed.
- No candidate or evidence-grade record was created.
- No VPS state, systemd timer, Hermes contract, or runtime deployment was touched.

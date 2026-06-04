# MCP Read-Only Upstream v1 Final Closure

Date: 2026-05-31

Task: `TASK-MCP-READONLY-UPSTREAM-V1-FINAL-CLOSURE-001`

This document closes `official-sources` as read-only upstream v1 for the current downstream
projects:

- `oposiciones2.0`
- `eduayudas`
- `la-ayuda`
- `renta-verificable`

This is a control-plane closure, not a product automation release.

## Boundary

Registry presence, registry capability fields, and runtime health remain separate signals.

In particular, `monitor_validated` and `monitor_support=available` mean that the source has
registered technical monitor support in `official-sources`. They do not mean that the source is
currently healthy, product-ready, candidate-ready, evidence-grade, safe for downstream automation,
or safe for publication.

## Final Upstream Status

```text
official-sources: CLOSED AS READ-ONLY UPSTREAM v1
operational_status: GO
candidate_creation_allowed: disabled for all registered sources
evidence_grade_allowed: disabled for all registered sources
writes: disabled unless a future explicit write contract says otherwise
source_expansion: frozen unless a future consumer smoke proves a concrete source gap
BOP_ALICANTE: recovered on 2026-06-02 after earlier DNS-dependent degraded/manual-review state
```

## Implemented MCP Consumer Surface

Current consumer-facing read-only tools:

```text
recommend_sources_for_consumer
list_case_taxonomy
build_evidence_packet
resolve_normative_reference
resolve_fiscal_reference
list_downstream_integration_smokes
check_downstream_integration_smokes
```

These tools provide source recommendations, stable demand classes, review-only packet/reference
profiles, and internal contract checks.

They do not write downstream projects, create candidates, create evidence-grade records, decide
legal/fiscal meaning, decide eligibility, approve publication, run downstream imports, send
notifications, or mutate the registry.

## Contract Stack

The v1 closure is defined by:

```text
docs/SOURCE_STATUS_CONTRACT.md
docs/MCP_CASE_TAXONOMY.md
docs/MCP_DOWNSTREAM_SOURCE_NEEDS_MATRIX.md
docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md
docs/MCP_DOWNSTREAM_INTEGRATION_CLOSURE.md
docs/architecture/downstream-integration-contracts.md
docs/MCP_TOOLS.md
```

Project-specific planning contracts:

```text
docs/MCP_EDUAYUDAS_EVIDENCE_PACKET_PROFILE.md
docs/MCP_LAAYUDA_SOURCE_RESOLVER_PROFILE.md
docs/MCP_RENTA_FISCAL_REFERENCE_PROFILE.md
```

## Acceptance Evidence

The upstream MCP smoke checker must pass:

```text
check_downstream_integration_smokes
```

Expected result:

```text
status=ok
resource_type=downstream_integration_smoke_run
count=4
passed_count=4
failed_count=0
downstream_commands_executed=false
monitor_previews_executed=false
live_fetches_performed=false
jsonl_written=false
registry_mutated=false
```

Source safety invariants:

```text
registered sources: 67
candidate_creation_allowed=false for 67/67 registered sources
evidence_grade_allowed=false for 67/67 registered sources
data/rss_monitor absent
data/html_monitor absent
```

## Downstream Handoff

The next phase is downstream acceptance, not upstream source expansion.

Each downstream project must run its own preview/import check:

| Consumer | Acceptance smoke | Upstream role |
| --- | --- | --- |
| `oposiciones2.0` | strict alert preview | Source recommendations and alert contract only |
| `eduayudas` | evidence JSON preview | Review-only evidence packet profile |
| `la-ayuda` | evidence/candidate preview | Manual-review normative source leads |
| `renta-verificable` | seed/reference validation | AEAT-first fiscal reference leads |

Passing upstream MCP smokes means only that `official-sources` returns the expected read-only
contracts. It does not mean downstream imports have run or downstream data is product-ready.

## Remaining Work Policy

After this closure, new upstream work is allowed only when a downstream acceptance smoke proves a
specific gap.

Allowed future work:

- a concrete missing source family required by a failing downstream smoke;
- a narrow schema/fixture adapter needed by a downstream preview;
- documentation of a product-side acceptance result;
- a separate recovery task for `BOP_ALICANTE` if explicitly reopened.

Not allowed under this closure:

- broad source expansion;
- generic provincial monitor waves;
- automatic candidate creation;
- evidence-grade promotion;
- downstream product writes;
- publication;
- tax, legal, eligibility, ranking, or approval conclusions.

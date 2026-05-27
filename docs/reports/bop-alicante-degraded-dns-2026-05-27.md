# BOP Alicante Degraded DNS Contract

Date: 2026-05-27

Task: `TASK-BOP-ALICANTE-DEGRADED-DNS-001`

## Decision

`BOP_ALICANTE` is formally treated as `degraded/manual-review` for provincial monitor health
reporting because its normal live preview currently fails during DNS resolution.

This is a health-reporting contract, not a registry promotion or demotion.

```text
healthy monitored provincial sources: 7
degraded monitored provincial sources: 1
combined all-sources health: PARTIAL-GO
all-sources-green claim: not allowed
Wave 003: unblocked only under partial-health criteria
```

## Source Classification

Healthy monitored provincial sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_LUGO
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
```

Degraded monitored provincial sources:

```text
BOP_ALICANTE
reason: resolver-dependent DNS instability for sede.diputacionalicante.es
normal preview result: httpx.ConnectError: [Errno 11002] getaddrinfo failed
```

## Registry Contract

No `config/sources.yaml` change is made in this task.

Rationale:

```text
the registry operational_status enum has no degraded/manual-review value
adding a new enum value would be a broader registry-model change
BOP_ALICANTE remains in the registry
BOP_ALICANTE does not revert to inventory_only
BOP_ALICANTE is not marked healthy for live health gates
candidate_creation_allowed remains false
evidence_grade_allowed remains false
```

The existing `monitor_validated` status is treated as historical parser/endpoint validation. Current
live health reporting must additionally account for the degraded DNS state documented here.

## Evidence Basis

This contract is based on:

```text
docs/reports/provincial-monitors-health-001-2026-05-27.md
docs/reports/bop-alicante-health-regression-2026-05-27.md
```

Summary:

```text
PR #13 health check:
  seven monitored provincial sources returned metadata-only preview records
  BOP_ALICANTE failed twice with getaddrinfo failed

PR #14 diagnostic:
  endpoint official status: apparently current
  parser regression: not demonstrated
  endpoint obsolete: not demonstrated
  forced hostname resolution to Google DNS address returns parser-compatible JSON
  normal local resolver path still fails
```

## Operational Boundary

This task does not authorize:

```text
hard-coded IP routing
custom DNS-over-HTTPS resolution inside the monitor
DNS bypass
headless browser
PDF/artifact downloads
candidate creation
evidence-grade output
downstream writes
VPS checkout changes
Hermes config changes
systemd changes
timer changes
```

No live scraping or preview command was required for this contract task beyond relying on the
diagnostic evidence already recorded in the preceding report.

## Wave 003 Gate

Wave 003 may proceed only if the PR and follow-up task state this explicitly:

```text
provincial health gate: PARTIAL-GO
healthy set used for expansion: 7 sources
degraded source excluded from healthy set: BOP_ALICANTE
no claim that all 8 monitored provincial sources are healthy
```

If `BOP_ALICANTE` later recovers, run a separate live preview health check before moving it back
into the healthy set.

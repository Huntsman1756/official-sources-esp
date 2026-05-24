# Next Agent Handoff

Last updated: 2026-05-24

## Current Status

`TASK-SOURCE-PLATFORM-001` is accepted as the operative cross-project boundary.

Read first:

```text
PROJECT_STATE.md
docs/CROSS_PROJECT_INTEGRATION_MAP.md
docs/reports/CROSS_PROJECT_INTEGRATION_MAP_2026-05-24.md
```

## Active Guardrails

Do not perform new `oposiciones2.0` write actions from `official-sources`.

Do not convert alert-grade records into `source_candidates`.

Do not create product records from `official-sources`, including:

```text
PublicEmploymentProcess
ProcessEvent
ProcessMatch
aid_program
benefit markdown/page
tax conclusion
notification
user subscription
product ranking
```

Do not run DB or VPS operations unless a separate, source-specific task explicitly authorizes them.

Do not touch downstream repos from an `official-sources` platform task.

## Next Allowed Work

The next real work should be one of these, not several in parallel:

1. One source operation at a time in `official-sources`, with its own scope, validation, and report.
2. Product-local design/preview for draft process creation inside `oposiciones2.0`, not from this repo.
3. `EduAyudas` or `la-ayuda` evidence-grade work only after their dirty states/product fixes are clean.
4. `renta-verificable` source-needs audit before any integration work.

## Blocked Or Deferred Work

Blocked until separately approved:

- alert-grade storage implementation;
- alert-grade to evidence-grade automatic promotion;
- alert-grade to downstream publication;
- bulk imports;
- broad historical backfills;
- BDNS `concesiones`;
- product notifications or subscriptions;
- downstream publication from `official-sources`.

## Validation Baseline For Docs-Only Boundary Updates

Required validation for docs-only boundary updates:

```bash
git diff --check
```

Relevant docs consistency check:

```bash
git diff --name-only
```

Confirm the changed files are docs/control-plane files only and do not include source adapters,
tests that imply behavior changes, migrations, DB files, generated exports, or downstream paths.

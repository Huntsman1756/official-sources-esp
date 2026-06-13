# Hermes Freshness Schedule Policy

Task: `TASK-HERMES-FRESHNESS-SCHEDULE-POLICY-001`

Status: policy-only

Date: 2026-06-13

## Verdict

This policy defines how `official-sources hermes freshness-report` should be scheduled in a future
implementation. It does not create, modify, install, or activate any timer, service, deploy script,
VPS state, or runtime automation.

```text
PR scope: policy only
timer activation: forbidden
VPS deployment: forbidden
freshness role: report-only signal
repair role: forbidden
```

## Relationship To Strict Audit

Hermes strict audit and Hermes freshness report are separate signals.

```text
strict audit:
  purpose: release, worktree, registry-count, and contract drift health
  current scheduled path: official-sources hermes scheduled-audit
  existing report root: /var/lib/hermes-official-sources-auditor/reports
  strict NO-GO: may fail the scheduled strict-audit service

freshness report:
  purpose: runtime source freshness over existing monitor JSONL state
  current command: official-sources hermes freshness-report
  proposed report root: /var/lib/hermes-official-sources-auditor/freshness-reports
  initial scheduled behavior: report-only, no service-blocking enforcement
```

Freshness does not replace strict audit. A `GO` freshness report cannot override strict audit
`NO-GO`, and strict audit `GO` cannot prove source freshness.

## Proposed Command Shape

The runtime root must be the repository/runtime root that contains `data/...`, not the `data`
directory itself.

```bash
official-sources hermes freshness-report \
  --runtime-root . \
  --now "$UTC_NOW" \
  --default-threshold-hours 72 \
  --critical-source BOE \
  --critical-source BDNS \
  --critical-source BOCM \
  --expected-source BOE \
  --expected-source BDNS \
  --expected-source BOCM \
  --output /var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-$STAMP.md
```

The documented local smoke used `--runtime-root .` and returned `NO-GO` when the local checkout had
zero `data/*_monitor/*/*_discovery.jsonl` files. That behavior is correct and must be preserved:
empty runtime state must not produce an empty `GO`.

## Scheduling Policy

Recommended first schedule after implementation:

```text
cadence: once daily
preferred window: after expected BOE/BDNS/monitor refreshes and before human review time
initial mode: report-only
minimum observation period before enforcement: 7 successful scheduled runs
```

The first implementation should not modify the existing strict-audit service behavior. It should
write a freshness report and return process success if the report was generated, even when the
freshness verdict is `WARNING` or `NO-GO`.

## Exit-Code Policy

Initial report-only integration:

```text
report generated successfully, verdict GO: exit 0
report generated successfully, verdict WARNING: exit 0
report generated successfully, verdict NO-GO: exit 0
invalid args, unreadable runtime root, corrupt JSONL, or report write failure: exit non-zero
```

Later enforcement, only after a separate approval task:

```text
VERDICT: GO       -> exit 0
VERDICT: WARNING  -> exit 0
VERDICT: NO-GO    -> exit 1
```

The initial policy deliberately keeps "freshness is bad" separate from "the freshness auditor could
not run." This avoids activating a hard VPS blocker before real scheduled evidence exists.

## Report Location

Freshness reports should use a dedicated directory under the Hermes state root:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports/
```

This keeps strict release audit reports separate from source freshness reports while preserving the
same ownership and operational surface.

Suggested filename:

```text
hermes-freshness-report-YYYYMMDD-HHMMSS.md
```

The implementation must create only this report path and any required parent directory under the
freshness report root.

## Retention Policy

Initial retention:

```text
keep latest: 60 reports
delete policy: oldest freshness reports only
scope: /var/lib/hermes-official-sources-auditor/freshness-reports/
```

Retention must not delete strict audit reports, logs, source data, registry files, SQLite databases,
or downstream artifacts.

Retention can be implemented in a later PR. The first scheduler implementation may document manual
retention if automatic deletion would broaden the write surface.

## Operational Verdict Policy

```text
GO:
  - all expected critical sources have fresh runtime JSONL state, or documented calendar exception;
  - no corrupt JSONL or unreadable runtime evidence;
  - forbidden-action flags remain false.

WARNING:
  - non-critical source stale or missing;
  - source-specific cadence unclear;
  - report generated, but operator should review thresholds or expected-source list.

NO-GO:
  - expected critical source is missing;
  - expected critical source is stale beyond threshold without calendar exception;
  - runtime evidence is insufficient to prove freshness;
  - empty runtime state would otherwise produce an empty report.
```

`NO-GO` is a signal for human action. It must not trigger automatic `git pull`, materialization,
registry promotion, SQLite writes, evidence/candidate creation, publication, downstream execution,
or issue creation.

## Pre-Activation Checklist

Before any VPS timer or systemd integration is proposed:

```text
- PR #41-style manual smoke exists for local runtime state.
- A VPS manual smoke has been run without changing timers or services.
- The VPS command uses --runtime-root /opt/official-sources/app, not /opt/official-sources/app/data.
- The report root exists or can be created under the Hermes state root.
- The expected critical source list is explicit.
- The default threshold is explicit.
- A corrupt JSONL fixture/test remains covered.
- Empty runtime state is still fail-closed.
- The initial integration is report-only.
- No downstream smokes are added.
```

## Forbidden For The Scheduling PR

The future first implementation PR must not:

```text
- activate a systemd timer
- modify VPS services
- deploy to VPS
- run downstream smokes
- write SQLite
- run ingest-monitor-date
- mutate config/sources.yaml
- create official_documents
- create evidence records
- create candidates
- create publication artifacts
- open issues automatically
- change strict-audit enforcement behavior
```

Any timer activation, VPS deployment, or hard `NO-GO` enforcement must be a later task with its own
manual smoke and review.

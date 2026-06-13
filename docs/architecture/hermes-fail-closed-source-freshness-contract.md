# Hermes Fail-Closed Source Freshness Contract

Task: `TASK-HERMES-FAIL-CLOSED-SOURCE-FRESHNESS-001`

Status: contract-only

Date: 2026-06-13

## Verdict

This contract defines the next Hermes improvement as a fail-closed freshness and smoke auditor.
It does not implement runtime code, systemd changes, VPS deployment, source expansion, database
writes, downstream writes, or automatic repair.

Hermes remains a judge, not an operator.

```text
Hermes role: watchdog/auditor
write/promote/publish role: forbidden
automatic repair role: forbidden
source freshness automation: report-only until a later implementation PR
```

## Purpose

The current Hermes drift auditor proves release and repository health. The freshness contract adds
a second layer: whether source monitor state and downstream-facing read-only smoke contracts are
fresh enough to trust.

The goal is to make stale source state visible without granting Hermes authority to fix it.

## Allowed Actions

Future implementations under this contract may:

```text
- read the source registry
- read existing monitor metadata and cache timestamps
- read existing SQLite metadata in read-only mode
- read scoped systemd unit/timer state and journal evidence
- run in-process read-only MCP/planner smokes
- write local Hermes audit reports and logs under the Hermes state root
- emit GO, WARNING, or NO-GO
- optionally open or append a human-review report if explicitly implemented later
```

## Forbidden Actions

Future implementations under this contract must not:

```text
- run git pull, git fetch, git reset, git checkout, or merge commands
- mutate config/sources.yaml
- create or update official_documents
- create or update evidence records
- create or update candidates
- create source-registry promotions
- download PDFs or artifacts
- run monitor materialization commands
- run ingest-monitor-date
- write to downstream product repositories
- publish downstream outputs
- modify systemd units or timers
- deploy code or restart services
- self-repair failed sources
```

If any future implementation needs one of those actions, it must be a separate operator task, not
Hermes freshness automation.

## Source Freshness SLOs

These SLOs define default thresholds. Source-specific overrides may be added only when documented
in the contract or in the source registry metadata.

Official sources do not all publish daily. A stale timestamp is `WARNING` by default unless the
source is marked critical and the report can prove that the source missed its own expected cadence.
Weekends, public holidays, no-publication days, and source-specific discontinuous schedules must be
represented as documented calendar exceptions, not treated as automatic `NO-GO`.

| Source family | WARNING | NO-GO |
| --- | --- | --- |
| `BOE` daily monitor state | No successful update or current-day/no-publication explanation for more than 36 hours. | No successful update or documented no-publication explanation for more than 72 hours, except documented weekend/holiday gaps. |
| `BDNS` cache/state | Cache or latest observed state older than 24 hours. | Cache or latest observed state older than 72 hours when a downstream contract depends on current BDNS state. |
| Critical RSS/API/HTML monitors | Latest successful sample outside the source-specific threshold. | Critical source stale beyond threshold and no documented fallback or no-publication explanation. |
| Non-critical RSS/API/HTML monitors | Latest successful sample outside the source-specific threshold. | Normally not global NO-GO; escalate to manual review unless explicitly marked critical. |
| Inventory-only sources | No freshness SLO. | No freshness SLO unless a future task promotes the source into a monitored contract. |

Freshness is about observed monitor state. It is not candidate readiness, evidence readiness,
publication readiness, or downstream product readiness.

## Downstream Read-Only Smokes

The freshness auditor may include read-only smoke checks for the current downstream integration
matrix. These smokes must execute only official-sources in-process read-only contracts, such as
`check_downstream_integration_smokes`.

Expected consumers:

```text
- eduayudas
- oposiciones2.0
- la-ayuda
- renta-verificable
```

These checks may validate expected planner fields, status envelopes, and forbidden-action flags.
They must not run downstream imports, previews, shells, product commands, live fetches, or writes.

## Verdict Rules

```text
GO:
  - all critical freshness checks are within threshold, or have a documented no-publication reason;
  - read-only downstream smokes pass;
  - no forbidden action is observed.

WARNING:
  - non-critical freshness is stale;
  - optional cache evidence is missing;
  - a downstream read-only smoke is inconclusive but not contract-breaking;
  - repeated warnings require human triage but do not grant Hermes repair authority.

NO-GO:
  - a critical source is stale beyond threshold without documented fallback;
  - a required downstream read-only smoke violates its expected safety envelope;
  - the freshness auditor observes or requires a forbidden action;
  - the report cannot prove which source, timestamp, cache, or smoke produced the finding.
```

## Minimum Report Format

Each future freshness report should include at least:

```yaml
contract: hermes-fail-closed-source-freshness
contract_version: 1
generated_at: "YYYY-MM-DDTHH:MM:SSZ"
repo_head: "<sha>"
verdict: GO|WARNING|NO-GO
checks:
  - check_id: "<stable id>"
    family: "BOE|BDNS|RSS|API|HTML|downstream_smoke"
    source_code: "<optional source code>"
    status: GO|WARNING|NO-GO
    severity: critical|non_critical|optional
    latest_success_at: "<timestamp or null>"
    latest_record_date: "<date or null>"
    staleness_hours: 0
    threshold_hours: 0
    calendar_exception: "<weekend, holiday, no_publication, source_specific, or null>"
    evidence: "<path, query, or report section>"
    impact: "<operator-facing impact>"
    action_required: "<human action, or none>"
forbidden_actions_confirmed:
  git_mutation: false
  registry_mutated: false
  official_documents_written: false
  evidence_created: false
  candidates_created: false
  artifacts_downloaded: false
  downstream_writes: false
  publication_created: false
  systemd_mutated: false
```

The report must be legible to an operator without requiring log archaeology.

## Escalation

Warnings and NO-GO findings are escalation signals only.

```text
WARNING:
  - record the finding in the daily report;
  - optionally create or append a human-review issue after repeated occurrences;
  - do not repair automatically.

NO-GO:
  - fail closed in the report and, if implemented in a scheduled command, exit non-zero;
  - state the exact source, timestamp, smoke, or missing proof that caused the failure;
  - require a separate operator task for any fix, ingestion, materialization, deploy, or promotion.
```

## Separation From Operator Materialization

`ingest-monitor-date` is an operator-controlled persistent SQLite materialization command. It may
write `ingestion_runs`, runtime `official_sources`, and `official_documents` when explicitly
invoked by an operator against a selected database.

Hermes freshness must not invoke `ingest-monitor-date`.

Hermes freshness may only report that a materialization path appears stale, missing, or unhealthy.
Any materialization rerun remains a separate human-controlled operation.

## Acceptance Criteria For A Future Implementation PR

A future implementation PR can be reviewed against this contract only if:

```text
- it keeps Hermes read-only with respect to registry, SQLite domain tables, evidence, candidates,
  artifacts, downstream projects, publication outputs, git state, and systemd;
- it writes only Hermes-owned reports/logs;
- it has deterministic tests for GO, WARNING, and NO-GO freshness outcomes;
- it tests forbidden-action flags or equivalent guardrails;
- it documents local validation and any VPS follow-up separately;
- it does not alter source parsers, monitor materialization, downstream products, or deployment.
```

If the implementation also needs downstream product smokes beyond in-process official-sources
contracts, that work should be split into a later task.

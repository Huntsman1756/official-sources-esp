# Hermes Freshness Timer Activation Smoke - 2026-06-14

Task:

```text
TASK-HERMES-FRESHNESS-TIMER-ACTIVATION-SMOKE-001
```

## Scope

VPS activation smoke after PR #59 merged.

This smoke activates the report-only timer and validates the underlying service manually.
It does not wait for the first scheduled run.

## VPS State

```text
VPS checkout before update: b42baa7
VPS checkout after update: 319deb0
branch: main
worktree: clean
```

Full release SHA:

```text
319deb05f97f6211111a50be91af4dec672b9062
```

## Installed Timer

Timer:

```text
/etc/systemd/system/official-sources-hermes-freshness-report.timer
```

Unit content:

```ini
[Timer]
OnCalendar=*-*-* 08:15:00 UTC
Persistent=true
RandomizedDelaySec=5m
Unit=official-sources-hermes-freshness-report.service
```

Activation command:

```bash
systemctl enable --now official-sources-hermes-freshness-report.timer
```

Observed state:

```text
official-sources-hermes-freshness-report.timer: enabled
timer state: active (waiting)
trigger observed: 2026-06-14 08:19:28 UTC
triggered service: official-sources-hermes-freshness-report.service
```

## Manual Service Validation After Timer Activation

Command:

```bash
systemctl start official-sources-hermes-freshness-report.service
```

Result:

```text
FRESHNESS_SERVICE_START_EXIT=0
service status: inactive (dead)
process status: 0/SUCCESS
freshness_exit_code=0
```

Generated files:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-20260614-044301.md
/var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl
```

Freshness verdict:

```text
VERDICT: GO
```

Critical sources:

```text
BDNS healthy age=0.0h
BOCM healthy age=4.7h
BOE healthy age=4.7h
```

## Strict Audit

An initial strict audit returned `NO-GO` because the external release contract was written with
an incorrect SHA:

```text
expected_head_sha: 319deb068a5d2a4f0533b4c6b28f328dcf6dfdf7
actual_head_sha:   319deb05f97f6211111a50be91af4dec672b9062
```

This was a contract transcription error, not a code or worktree drift. The contract was corrected
to the exact local/VPS/remote SHA:

```text
expected_head_sha: 319deb05f97f6211111a50be91af4dec672b9062
```

After correction:

```text
STRICT_AUDIT_SERVICE_START_EXIT=0
strict report: /var/lib/hermes-official-sources-auditor/reports/strict-release-audit-20260614-044338.md
VERDICT: GO
actual_head_sha: 319deb05f97f6211111a50be91af4dec672b9062
remote_head_observed_sha: 319deb05f97f6211111a50be91af4dec672b9062
git_worktree_clean: True
Failed gates: none
Warnings: none
```

Systemd:

```text
systemctl --failed: 0 loaded units listed
```

## Forbidden Actions Confirmed

```text
auto-fix: no
git pull from timer/service: no
registry mutation: no
SQLite writes: no
ingest-bdns-*: no
ingest-monitor-date: no
strict-audit gate change: no
official_documents/evidence/candidates/publication: no
downstream writes: no
```

## Pending Scheduled Validation

The timer is active, but the first scheduled run has not been observed in this smoke.

Follow-up task:

```text
TASK-HERMES-FRESHNESS-TIMER-SCHEDULED-VALIDATION-001
```

Acceptance for the follow-up:

```text
- timer fires at its scheduled time
- service exits 0
- freshness report is written
- BOE/BDNS/BOCM are present
- strict audit remains GO
- systemctl --failed remains 0
```

## Verdict

```text
TASK-HERMES-FRESHNESS-TIMER-ACTIVATION-SMOKE-001: GO
timer activation: GO
manual service validation after activation: GO
strict audit after contract correction: GO
first scheduled run validation: pending
```

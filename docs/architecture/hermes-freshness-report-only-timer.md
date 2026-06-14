# Hermes Freshness Report-Only Timer

Status: implemented locally, not activated

Task:

```text
TASK-HERMES-FRESHNESS-REPORT-ONLY-TIMER-001
```

## Purpose

Add a systemd timer for the already validated freshness report-only service.

The timer does not change the service contract. It only schedules:

```text
official-sources-hermes-freshness-report.service
```

## Schedule

```text
OnCalendar=*-*-* 08:15:00 UTC
Persistent=true
RandomizedDelaySec=5m
```

The time is deliberately after the BOE daily timer:

```text
00:15 UTC strict audit
07:30 UTC BOE daily
08:15 UTC freshness report
12:00 UTC integrity check
```

## Runtime Contract

Allowed writes remain limited to:

```text
/var/lib/hermes-official-sources-auditor/freshness-runtime/
/var/lib/hermes-official-sources-auditor/freshness-observations/
/var/lib/hermes-official-sources-auditor/freshness-reports/
```

Forbidden:

```text
- auto-fix
- git pull
- registry mutation
- SQLite writes
- ingest-bdns-*
- ingest-monitor-date
- strict-audit gate changes
- official_documents
- evidence
- candidates
- publication
- downstream writes
```

## Activation Gate

The PR adds the timer file only. The merge itself does not enable or start the timer.

Activation on VPS must be explicit:

```bash
systemctl daemon-reload
systemctl enable --now official-sources-hermes-freshness-report.timer
systemctl status official-sources-hermes-freshness-report.timer --no-pager
systemctl list-timers --all | grep freshness
```

After activation, perform a manual service validation:

```bash
systemctl start official-sources-hermes-freshness-report.service
systemctl status official-sources-hermes-freshness-report.service --no-pager
systemctl --failed --no-pager
```

## Follow-Up

The first scheduled run must be documented separately:

```text
TASK-HERMES-FRESHNESS-TIMER-SCHEDULED-VALIDATION-001
```

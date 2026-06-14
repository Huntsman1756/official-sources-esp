# Hermes Freshness Report-Only Schedule Integration

Status: implemented locally, service-only

Task:

```text
TASK-HERMES-FRESHNESS-REPORT-ONLY-SCHEDULE-INTEGRATION-001
```

## Purpose

Define the first programmatic entrypoint for critical-source freshness after the local and VPS
manual smokes proved:

```text
BOE: healthy
BDNS: healthy
BOCM: healthy
freshness report: VERDICT GO
strict audit after smoke: GO
systemctl --failed: 0
```

This integration remains report-only. It does not repair sources and it does not publish anything.

## Runtime Flow

`official-sources hermes scheduled-freshness-report` now performs a complete critical-source
report-only run:

```text
1. Run BOE RSS monitor into freshness-runtime.
2. Run BOCM RSS observation wrapper into freshness-runtime.
3. Run BDNS observation wrapper into freshness-runtime.
4. Run freshness-observations into latest-critical.jsonl.
5. Run freshness-report from latest-critical.jsonl into freshness-reports.
```

The report content may be `VERDICT: GO`, `WARNING`, or `NO-GO`. A generated `NO-GO` remains report
content, not an auto-fix trigger.

## Systemd Surface

Added service:

```text
deploy/systemd/official-sources-hermes-freshness-report.service
```

Added wrapper:

```text
deploy/systemd/run-official-sources-hermes-freshness-report.sh
```

No timer is added in this PR.

The service is intended to be installed and smoke-tested manually before any timer exists:

```bash
systemctl start official-sources-hermes-freshness-report.service
systemctl status official-sources-hermes-freshness-report.service --no-pager
```

## Write Surface

Allowed writes:

```text
/var/lib/hermes-official-sources-auditor/freshness-runtime/
/var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl
/var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-*.md
```

Forbidden writes:

```text
config/sources.yaml
SQLite databases
official_documents
evidence
candidates
publication
downstream/product repositories
systemd timers
```

## Boundaries

Allowed:

```text
- execute BOE RSS observation
- execute BOCM RSS observation wrapper
- execute BDNS observation wrapper
- compact observations to latest-critical.jsonl
- write one freshness markdown report
- return non-zero for operational failures such as command failure or missing output files
```

Forbidden:

```text
- auto-fix
- git pull
- registry mutation
- SQLite writes
- ingest-bdns-*
- ingest-monitor-date
- evidence/candidates/publication
- downstream smokes
- strict-audit gate changes
- timer activation
```

## Manual VPS Smoke Gate

Before adding any timer, run a separate VPS smoke that proves:

```text
systemctl start official-sources-hermes-freshness-report.service -> success
freshness report file written by official-sources user
latest-critical.jsonl written by official-sources user
BOE/BDNS/BOCM present in the report
strict audit after smoke -> GO
systemctl --failed -> 0
worktree clean
```

Only after that smoke should a timer task be opened.

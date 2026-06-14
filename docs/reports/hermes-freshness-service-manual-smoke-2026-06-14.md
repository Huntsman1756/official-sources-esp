# Hermes Freshness Service Manual Smoke - 2026-06-14

Task:

```text
TASK-HERMES-FRESHNESS-SERVICE-MANUAL-SMOKE-001
```

## Scope

Manual VPS smoke for PR #57 after merge.

This smoke validates the service-only report runner before any timer exists.

## VPS State

```text
VPS checkout before update: abd7a4f
VPS checkout after update: 3320f44
branch: main
worktree: clean
strict-audit contract expected_head_sha: 3320f44a6c4b7f1d73084b67905e0ff3872a4ebf
```

Installed files:

```text
/etc/systemd/system/official-sources-hermes-freshness-report.service
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-freshness-report.sh
```

Unit state:

```text
official-sources-hermes-freshness-report.service static
freshness timer installed: no
```

## Commands

```bash
cd /opt/official-sources/app
git fetch origin main
git merge --ff-only origin/main

install -o official-sources -g official-sources -m 0755 \
  deploy/systemd/run-official-sources-hermes-freshness-report.sh \
  /opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-freshness-report.sh

install -o root -g root -m 0644 \
  deploy/systemd/official-sources-hermes-freshness-report.service \
  /etc/systemd/system/official-sources-hermes-freshness-report.service

systemctl daemon-reload
systemctl start official-sources-hermes-freshness-report.service
systemctl status official-sources-hermes-freshness-report.service --no-pager
journalctl -u official-sources-hermes-freshness-report.service -n 80 --no-pager
```

## Service Result

```text
SERVICE_START_EXIT=0
service state after run: inactive (dead)
systemd result: Deactivated successfully
freshness_exit_code=0
```

Journal output:

```text
report_path=/var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-20260614-043642.md
observations_path=/var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl
freshness_exit_code=0
```

## Freshness Result

Report:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-20260614-043642.md
```

Verdict:

```text
VERDICT: GO
```

Sources:

```text
BDNS healthy age=0.0h
BOCM healthy age=4.6h
BOE healthy age=4.6h
```

Observation JSONL:

```text
/var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl
```

Observation inputs:

```text
BDNS input_kind=api_monitor_jsonl
BDNS reason=derived from operator-controlled BDNS latest API observation

BOCM input_kind=rss_monitor_jsonl
BOCM reason=derived from monitor discovered_at

BOE input_kind=rss_monitor_jsonl
BOE reason=derived from monitor discovered_at
```

Ownership:

```text
/var/lib/hermes-official-sources-auditor/freshness-runtime       official-sources:official-sources
/var/lib/hermes-official-sources-auditor/freshness-observations official-sources:official-sources
/var/lib/hermes-official-sources-auditor/freshness-reports      official-sources:official-sources
```

## Post-Smoke Strict Audit

Command:

```bash
systemctl start official-sources-hermes-auditor.service
```

Result:

```text
STRICT_AUDIT_SERVICE_START_EXIT=0
strict_exit_code=0
strict report: /var/lib/hermes-official-sources-auditor/reports/strict-release-audit-20260614-043708.md
```

Strict verdict:

```text
VERDICT: GO
expected_head_sha: 3320f44a6c4b7f1d73084b67905e0ff3872a4ebf
actual_head_sha: 3320f44a6c4b7f1d73084b67905e0ff3872a4ebf
remote_head_observed_sha: 3320f44a6c4b7f1d73084b67905e0ff3872a4ebf
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
timer added: no
timer enabled: no
git pull from service: no
registry mutation: no
SQLite writes: no
ingest-bdns-*: no
ingest-monitor-date: no
official_documents/evidence/candidates/publication: no
downstream writes: no
strict-audit gate change: no
auto-fix: no
```

## Verdict

```text
TASK-HERMES-FRESHNESS-SERVICE-MANUAL-SMOKE-001: GO
service manual smoke: GO
critical freshness report: GO
strict audit after smoke: GO
timer activation: still not done
```

The next task may add a report-only timer, but it must remain separate from this smoke.

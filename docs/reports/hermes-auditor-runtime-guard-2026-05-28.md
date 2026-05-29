# Hermes Auditor Runtime Guard - 2026-05-28

Task: `TASK-HERMES-AUDITOR-RUNTIME-GUARD-001`

## Verdict

GO.

The VPS Hermes auditor now has operational guards against overlapping or runaway executions.

## VPS Changes

These changes were applied on the VPS only. The runner and systemd drop-in are operational files,
not versioned files in this repository.

Runner updated:

```text
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh
```

The runner now acquires a non-blocking lock before auditing:

```text
lock: /var/lib/hermes-official-sources-auditor/hermes-auditor.lock
skip output: skipped=concurrent_existing_run lock=/var/lib/hermes-official-sources-auditor/hermes-auditor.lock
skip exit status: 0
```

Systemd drop-in added:

```text
/etc/systemd/system/official-sources-hermes-auditor.service.d/runtime-guard.conf
```

Effective setting:

```text
TimeoutStartSec=5min
```

`RuntimeMaxSec` was not used because systemd reports that it has no effect for this
`Type=oneshot` service. `TimeoutStartSec=5min` is the effective runtime guard for the auditor
`ExecStart`.

## Validation

Syntax and systemd validation:

```text
bash -n /opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh
systemd-analyze verify official-sources-hermes-auditor.service
systemctl daemon-reload
systemctl show official-sources-hermes-auditor.service -p TimeoutStartUSec
```

Observed result:

```text
TimeoutStartUSec=5min
```

Anti-overlap test:

```text
skip_status=0
skip_output=skipped=concurrent_existing_run lock=/var/lib/hermes-official-sources-auditor/hermes-auditor.lock
```

Manual service smoke after the guard:

```text
official-sources-hermes-auditor.service: Result=success
ExecMainStatus=0
ActiveState=inactive
SubState=dead
```

Latest smoke report:

```text
/var/lib/hermes-official-sources-auditor/reports/vps-audit-20260528-180136.md
```

Report signals:

```text
target_repo: /opt/official-sources/app
git_branch: main
git_commit: 08becb29162a8b896eedb91a7c8c33c4c8f6b79c
git_worktree: clean
rss_monitor: present
```

System state:

```text
systemctl --failed: 0 loaded units listed
```

Ownership:

```text
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh: official-sources:official-sources
/var/lib/hermes-official-sources-auditor/hermes-auditor.lock: official-sources:official-sources
```

## Boundaries

This task did not change:

```text
official-sources-hermes-auditor.timer calendar
RandomizedDelaySec
Hermes model settings
source registry
RSS monitor logic
provincial monitor logic
candidate/evidence-grade records
downstream writes
VPS checkout HEAD
```

The VPS checkout remained:

```text
/opt/official-sources/app
branch: main
commit: 08becb29162a8b896eedb91a7c8c33c4c8f6b79c
worktree: clean
```

## Operational Note

Future `git fetch`, `git status`, and `git pull --ff-only` operations inside
`/opt/official-sources/app` should run as `official-sources`, not `root`, to avoid ownership drift.

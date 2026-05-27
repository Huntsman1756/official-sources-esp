# Hermes auditor canonical root - 2026-05-27

Task: `TASK-HERMES-AUDITOR-CANONICAL-ROOT-001`

## Decision

Status:

```text
COMPLETED
Manual validation: GO
Scheduled validation: pending next timer run
```

The first valid Hermes report after the canonical-root fix is:

```text
/var/lib/hermes-official-sources-auditor/reports/vps-audit-20260527-044105.md
```

Hermes reports generated before `2026-05-27 04:41 UTC` should be treated as stale or
non-authoritative for operational decisions because they targeted or reasoned from obsolete context.

## Root Cause

Hermes was executing successfully, but it audited an obsolete checkout:

```text
/opt/official-sources/auditor-app
branch: codex/task-source-registry-001
commit: 9e7f6bb
PROJECT_STATE.md date: 2026-05-24
```

The canonical operational checkout is:

```text
/opt/official-sources/app
branch: main
commit at validation: 9ebf849f1663642071f60023385acc44c9fe5875
```

Because the prompt and environment pointed at stale context, Hermes recommended
`TASK-SOURCE-RSS-MONITOR-001` and reported that no RSS monitor existed. That was false for the
current operational repository.

## VPS Changes

These changes were applied on the VPS and are documented in this repository. The systemd drop-in
and runner script paths below are not versioned files in this repo.

The fix keeps runner/tooling and audited repository separate:

```text
/opt/hermes-official-sources-auditor/... = runner/tooling
/opt/official-sources/app = audited repository
/opt/official-sources/auditor-app = not operational source of truth
```

Systemd drop-in added:

```text
/etc/systemd/system/official-sources-hermes-auditor.service.d/canonical-root.conf
```

It defines:

```ini
[Service]
Environment=APP_ROOT=/opt/official-sources/app
Environment=REPO_ROOT=/opt/official-sources/app
Environment=TARGET_REPO=/opt/official-sources/app
```

Runner updated:

```text
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh
```

Runner backups left on the VPS:

```text
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh.bak-20260527-043357
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh.bak-20260527-044054
```

The runner now:

- audits `TARGET_REPO=/opt/official-sources/app`;
- records audited path, branch, commit, worktree state, `PROJECT_STATE.md` date, and RSS monitor
  presence before invoking Hermes;
- gathers local read-only preflight evidence from systemd status, timers, resources, and project
  docs;
- invokes Hermes with empty toolsets (`-t ''`) so the nocturnal auditor does not try SSH, sudo, or
  browser/tooling paths;
- uses a neutral prompt that does not assume historical tasks are still open.

## Validation

Manual service run:

```text
official-sources-hermes-auditor.service: status=0/SUCCESS
```

Final checks:

```text
systemctl --failed -> 0 loaded units listed
official-sources-hermes-auditor.timer -> active/waiting
official-sources-boe-daily.timer -> active/waiting
official-sources-integrity-check.timer -> active/waiting
official-sources-boe-daily.service -> inactive/dead, last status=0/SUCCESS
official-sources-integrity-check.service -> inactive/dead, last status=0/SUCCESS
```

Valid report evidence:

```text
target_repo: /opt/official-sources/app
git_branch: main
git_commit: 9ebf849f1663642071f60023385acc44c9fe5875
git_worktree: clean
project_state_date: 2026-05-26
rss_monitor: present
TASK-SOURCE-RSS-MONITOR-001: implemented locally / already completed
```

The valid report no longer recommends `TASK-SOURCE-RSS-MONITOR-001` as current work.

## Known Notes

The runner intentionally avoids interactive Hermes tools for this nocturnal auditor. This makes the
output less exploratory but more reproducible and local-first.

`Reached maximum iterations` did not appear in the valid report. If it appears in future scheduled
runs, treat it as a warning unless the report is incomplete or reintroduces stale task
recommendations.

The scheduled validation is still pending. The next timer run should confirm the same canonical
root without manual intervention.

## Follow-up Validation

After the next automatic run, check:

```bash
systemctl status official-sources-hermes-auditor.timer --no-pager
systemctl status official-sources-hermes-auditor.service --no-pager
systemctl --failed
ls -lt /var/lib/hermes-official-sources-auditor/reports | head
```

Then inspect the latest report:

```bash
LATEST="$(ls -t /var/lib/hermes-official-sources-auditor/reports/vps-audit-*.md | head -1)"
grep -E "target_repo|git_branch|git_commit|git_worktree|rss_monitor|TASK-SOURCE-RSS-MONITOR-001" "$LATEST"
grep -i "Reached maximum iterations" "$LATEST" || true
```

Expected evidence:

```text
target_repo: /opt/official-sources/app
git_branch: main
git_worktree: clean
rss_monitor: present
TASK-SOURCE-RSS-MONITOR-001: implemented/completed/not current work
```

Do not modify BOE daily, integrity-check, source registry, RSS monitor logic, or downstream writes
for the scheduled validation.

# Post-merge checklist - Hermes Drift Auditor

Scope: execute only after PR #29 has been merged into `main`.

Do not use this checklist as evidence that the VPS is already aligned. It is an operational plan for
the release-alignment step after merge.

## 1. Confirm final main SHA

```bash
git switch main
git pull --ff-only
git rev-parse HEAD
git status --short
```

Record the final `main` SHA. Do not assume it is `2dfbf10...`; GitHub merge strategy may create a
different commit.

## 2. Decide release contract update

If the merged Hermes drift auditor is now part of the approved release, update:

```text
config/hermes/audit_contract.yaml
```

Set:

```yaml
expected_head_sha: "<final-main-sha>"
```

Do not update this field before PR #29 is merged.

## 3. Validate locally

```bash
ruff check src tests
python -m pytest -q
official-sources hermes audit
```

Expected result before VPS alignment may still be `NO-GO` if the local or VPS state does not match
the new contract.

## 4. Create micro-close commit or PR if needed

Commit only the contract/state closure if `expected_head_sha` changed.

Suggested commit:

```bash
git commit -m "chore(hermes): update drift audit release contract"
```

## 5. VPS fast-forward only after contract closure

On VPS, perform controlled fast-forward only. Do not reset blindly.

Required checks:

```bash
cd /opt/official-sources/app
git status --short
git rev-parse HEAD
git ls-remote origin main
```

Proceed only if there is no dirty worktree requiring investigation.

## 6. Run VPS validation

```bash
official-sources hermes audit
systemctl --failed
systemctl status official-sources-hermes-auditor.timer --no-pager
```

Expected final closure:

```text
VPS HEAD == expected_head_sha
worktree clean
PROJECT_STATE fresh
source count == 67
inventory_only == DOUE only
systemctl --failed == 0
Hermes drift audit verdict == GO
```

## 7. Close task only with evidence

Close `TASK-HERMES-DRIFT-AUDITOR-001` only after the repo and VPS layers both have evidence.

Do not mark VPS aligned based only on PR merge.

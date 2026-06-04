# Post-merge checklist - Hermes Drift Auditor

Scope: execute only after PR #29 has been merged into `main`.

Do not use this checklist as evidence that the VPS is already aligned. It is an operational plan for
the release-alignment step after merge. The release SHA contract lives outside the audited checkout.

## 1. Confirm final main SHA

```bash
git switch main
git pull --ff-only
git rev-parse HEAD
git status --short
```

Record the final `main` SHA from `main` itself. Do not assume it is any branch commit; GitHub merge
strategy may create a different commit.

## 2. Prepare the external release contract

If the merged Hermes drift auditor is now part of the approved release, prepare an external runtime
contract outside the repository checkout:

```text
/etc/official-sources/hermes-audit-contract.yaml
```

Example shape:

```yaml
release:
  expected_head_sha: "<final-main-sha>"
  expected_branch: "main"
  approved_at: "2026-06-03T20:35:45Z"
  approved_reason: "PR #30 source coverage closeout + PR #29 Hermes drift auditor merged"
```

Do not store `expected_head_sha` in `config/hermes/audit_contract.yaml`. A versioned file inside
the audited checkout cannot honestly contain the final SHA of the commit that contains it.

## 3. Validate locally

```bash
ruff check src tests
python -m pytest -q
official-sources hermes audit
```

Expected local/dev result without the external release contract is `WARNING`, with no hard HEAD
gate. Strict mode should be reserved for the runtime path that has the external contract.

## 4. Validate strict mode with an external contract

When the external contract exists, strict mode should use it explicitly:

```bash
official-sources hermes audit \
  --release-contract /etc/official-sources/hermes-audit-contract.yaml \
  --strict-release-contract
```

Expected behavior:

```text
external contract present + HEAD match: GO, unless another gate fails
external contract present + HEAD mismatch: NO-GO
external contract missing + --strict-release-contract: NO-GO
external contract missing without strict mode: WARNING
```

## 5. VPS fast-forward only after contract closure

On VPS, perform controlled fast-forward only. Do not reset blindly. Do not create or update the
external release contract until the release SHA is approved.

Required checks:

```bash
cd /opt/official-sources/app
git status --short
git rev-parse HEAD
git ls-remote origin main
```

Proceed only if there is no dirty worktree requiring investigation.

## 6. Run VPS validation

Use strict mode on VPS:

```bash
official-sources hermes audit \
  --release-contract /etc/official-sources/hermes-audit-contract.yaml \
  --strict-release-contract
systemctl --failed
systemctl status official-sources-hermes-auditor.timer --no-pager
```

Expected final closure:

```text
VPS HEAD == external expected_head_sha
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

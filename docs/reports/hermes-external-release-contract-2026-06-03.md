# Hermes External Release Contract - 2026-06-03

Task: `TASK-HERMES-EXTERNAL-RELEASE-CONTRACT-002`

## Verdict

Implemented locally. Do not deploy yet.

Hermes now separates the versioned audit contract from the runtime release contract. The in-repo
contract defines stable audit rules; the external contract defines the approved deployment SHA.
This avoids the self-referential commit-SHA loop where updating `expected_head_sha` inside the
repo necessarily creates a new commit with a different SHA.

## Contract Layers

In-repo contract:

```text
config/hermes/audit_contract.yaml
```

Contains:

- `PROJECT_STATE.md` freshness policy;
- clean worktree requirement;
- source count contract;
- allowed `inventory_only` sources;
- registry parseability requirement;
- remote observation and journal evidence policy.

External runtime contract:

```text
/etc/official-sources/hermes-audit-contract.yaml
```

Contains:

```yaml
release:
  expected_head_sha: "<approved-main-sha>"
  expected_branch: "main"
  approved_at: "2026-06-03T20:35:45Z"
  approved_reason: "PR #30 source coverage closeout + PR #29 Hermes drift auditor merged"
```

## CLI

Local/dev mode can run without the external release contract:

```bash
official-sources hermes audit
```

If the external release contract is unavailable, local/dev mode reports:

```text
VERDICT: WARNING
external release contract unavailable; HEAD gate not enforced
```

VPS/release mode must use strict external-contract enforcement:

```bash
official-sources hermes audit \
  --release-contract /etc/official-sources/hermes-audit-contract.yaml \
  --strict-release-contract
```

Strict behavior:

```text
external contract present + HEAD match: GO, unless another gate fails
external contract present + HEAD mismatch: NO-GO
external contract missing + --strict-release-contract: NO-GO
external contract missing without strict mode: WARNING
```

## Safety

This change remains read-only:

- no deploy;
- no VPS checkout mutation;
- no `git pull`, `git fetch`, `git reset`, or `git checkout`;
- no systemd change;
- no source expansion;
- no candidates, evidence-grade records, artifacts, or downstream writes.

## Validation

Targeted validation:

```text
python -m pytest tests/test_hermes_drift_audit.py -q
```

Result:

```text
18 passed
```

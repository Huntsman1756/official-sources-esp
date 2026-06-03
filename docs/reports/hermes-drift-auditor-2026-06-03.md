# Hermes Drift Auditor - 2026-06-03

Task: `TASK-HERMES-DRIFT-AUDITOR-001`

## Verdict

Implemented locally.

Hermes now has a versioned read-only drift audit contract and a tested local evaluator that can be
called by the VPS runner without granting deploy or repository mutation authority.

## Scope

This task adds:

- `config/hermes/audit_contract.yaml`
- `src/official_sources/hermes_drift_audit.py`
- `official-sources hermes audit`
- `tests/test_hermes_drift_audit.py`
- `docs/examples/hermes_drift_audit_report_examples.md`

This task does not:

- deploy to VPS;
- run `git pull`, `git fetch`, `git reset`, or `git checkout`;
- mutate the audited repository during audit collection;
- change Hermes systemd timers or services;
- create candidates, evidence-grade records, artifacts, downstream writes, or source expansion.

## Gates

The audit evaluates:

- expected release SHA against the audited checkout HEAD;
- clean worktree requirement;
- minimum `PROJECT_STATE.md` date;
- optional remote `origin` head observation through `git ls-remote` only;
- source registry parseability;
- total source count;
- allowed `inventory_only` sources;
- journal evidence readability for scoped systemd units.

The current local contract expects:

```text
expected_head_sha=9df078b1ae599bdeca8c573bddbb53ea6c33a16a
expected_project_state_min_date=2026-06-02
require_clean_worktree=true
expected_total_sources=67
expected_inventory_only=DOUE
require_registry_parse=true
```

## CLI

The command is:

```bash
official-sources hermes audit \
  --contract config/hermes/audit_contract.yaml \
  --repo-root /opt/official-sources/app \
  --registry /opt/official-sources/app/config/sources.yaml \
  --project-state /opt/official-sources/app/PROJECT_STATE.md \
  --output /var/lib/hermes-official-sources-auditor/reports/hermes-drift-audit.md
```

By default, the command exits `0` when the audit was produced, even if the report verdict is
`NO-GO`. This keeps "auditor process ran" separate from "release is correct". Operators can add
`--fail-on-no-go` when a non-zero process status is desired.

## Report Contract

Each report ends with an explicit operational verdict:

```text
VERDICT: GO
VERDICT: WARNING
VERDICT: NO-GO
```

It also renders:

- observed state;
- failed gates;
- warnings;
- required human action.

Remote-head observation is deliberately informational unless the audited checkout `HEAD` itself
differs from the expected release SHA. A stale local tracking ref is not used. When remote
comparison is enabled, the command uses `git ls-remote`, which is read-only and does not mutate
local refs.

## Journal Evidence

Journal access is not treated as broad sudo authority. If `journalctl` cannot read the scoped units,
the report returns `WARNING` unless a stronger `NO-GO` reason already exists.

Preferred VPS hardening, if the service runs under a dedicated user:

```ini
SupplementaryGroups=systemd-journal
```

## Validation

Targeted tests:

```text
python -m pytest tests/test_hermes_drift_audit.py -q
```

Result:

```text
10 passed
```

Full validation:

```text
ruff check src tests
python -m pytest -q
```

Result:

```text
ruff: All checks passed
pytest: 756 passed, 2 warnings
```

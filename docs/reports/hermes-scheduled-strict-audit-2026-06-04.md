# Hermes Scheduled Strict Audit - 2026-06-04

Task: `TASK-HERMES-SCHEDULED-STRICT-AUDIT-003`

## Verdict

Implementation status is `GO for PR`.

Deployment status is `NO-GO until merge plus controlled VPS update`.

This change wires the versioned scheduled Hermes path to the deterministic strict release auditor:

```text
official-sources hermes audit \
  --release-contract /etc/official-sources/hermes-audit-contract.yaml \
  --strict-release-contract \
  --fail-on-no-go
```

The scheduled runner now returns the strict audit process status. A contractual `NO-GO` therefore
becomes a non-zero service exit code instead of a soft narrative-only finding.

## Scope

Added:

```text
src/official_sources/hermes_scheduled_audit.py
official-sources hermes scheduled-audit
deploy/systemd/run-official-sources-hermes-auditor.sh
deploy/systemd/official-sources-hermes-auditor.service
deploy/systemd/official-sources-hermes-auditor.timer
```

Updated tests:

```text
tests/test_hermes_drift_audit.py
tests/test_hermes_scheduled_audit.py
tests/test_systemd_templates.py
```

## Behavior

The scheduled runner:

- executes the strict drift audit with `--fail-on-no-go`;
- writes the strict audit report under `/var/lib/hermes-official-sources-auditor/reports`;
- writes a combined scheduled report and log under the same Hermes state root;
- keeps watchdog evidence such as `git rev-parse HEAD`, `git status --short`,
  `systemctl --failed`, and Hermes/BOE/integrity timer or service status;
- propagates the strict audit exit code as the scheduled command exit code;
- does not run `git pull`, `git fetch`, `git reset`, `git checkout`, deploy actions, or systemd
  mutations.

## Exit Policy

```text
VERDICT: GO       -> exit 0
VERDICT: WARNING  -> exit 0, if the CLI has no failed gates
VERDICT: NO-GO    -> exit 1 through --fail-on-no-go
```

This keeps warnings informational while making contractual drift fail the daily service.

## Deployment Boundary

No VPS change was performed in this implementation pass.

The current VPS remains aligned to the previously approved external contract until this PR is
merged and the operator performs the follow-up release alignment. Do not copy the new systemd
templates or wrapper to the VPS before merge.

After merge, the controlled VPS follow-up should:

```text
1. fast-forward /opt/official-sources/app to the approved origin/main SHA;
2. update /etc/official-sources/hermes-audit-contract.yaml to that same SHA;
3. install the versioned Hermes wrapper and service/timer templates;
4. run official-sources hermes scheduled-audit once manually;
5. verify official-sources-hermes-auditor.service fails on strict NO-GO and succeeds on GO;
6. leave the timer active for the next scheduled run.
```

## Validation

Executed locally:

```text
python -m pytest tests/test_hermes_scheduled_audit.py tests/test_hermes_drift_audit.py tests/test_systemd_templates.py -q
28 passed

ruff check src/official_sources/hermes_scheduled_audit.py tests/test_hermes_scheduled_audit.py tests/test_systemd_templates.py src/official_sources/cli.py tests/test_hermes_drift_audit.py
All checks passed
```

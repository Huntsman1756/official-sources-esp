# Hermes VPS Release Alignment - 2026-06-04

Task: `TASK-HERMES-VPS-RELEASE-ALIGNMENT-2026-06-04`

## Verdict

Operational closure is `GO`.

The repository, VPS checkout, and external Hermes release contract were aligned to this approved
release SHA during the operational closeout:

```text
68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a
```

Hermes strict audit on the VPS returned:

```text
VERDICT: GO
failed gates: none
warnings: none
```

## Evidence

```text
origin/main final: 68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a
previous VPS HEAD: a5c050b588fce8277247e9bcde3c446d852e784a
final VPS HEAD: 68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a
VPS branch: main
VPS worktree: clean
systemctl --failed: 0 loaded units listed
```

Hermes strict audit observed:

```text
expected_head_sha: 68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a
expected_head_sha_source: /etc/official-sources/hermes-audit-contract.yaml
actual_head_sha: 68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a
remote_head_observed_sha: 68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a
git_worktree_clean: True
project_state_date: 2026-06-03
source_count: 67
inventory_only_sources: ['DOUE']
```

## External Release Contract

Runtime path:

```text
/etc/official-sources/hermes-audit-contract.yaml
```

Ownership and permissions:

```text
root:root 0644
```

Contents:

```yaml
release:
  expected_head_sha: "68dcffa9aa59f60ab526e67ae0dd3a12ba192e5a"
  expected_branch: "main"
  approved_reason: "PR #30 source coverage closeout + PR #29 Hermes drift auditor + PR #31 external release contract"
  approved_at: "2026-06-03"
```

This report is evidence of the closeout run. It is not the live release contract. The live expected
deployment SHA is intentionally read from `/etc/official-sources/hermes-audit-contract.yaml`, not
from an in-repo Markdown file, so later documentation-only commits do not recreate a
self-referential release-SHA loop.

## Preserved VPS Drift

Before alignment, the VPS checkout had stale partial-release drift. It was preserved before any
release action:

```text
bundle: /var/tmp/official-sources-vps-drift-20260604-054135
stash: stash@{0}: pre-68dcffa-stale-vps-drift-preserved-20260604
stash applied: no
```

Classification:

```text
DRIFT_STALE_PARTIAL_RELEASE
```

The drift was not treated as a hotfix and was not reapplied after fast-forward.

## Actions Performed

Performed:

- preserved full dirty VPS diff under `/var/tmp`;
- stashed stale VPS drift;
- fast-forwarded `/opt/official-sources/app` to `origin/main`;
- created `/etc/official-sources/hermes-audit-contract.yaml`;
- ran Hermes strict audit from the VPS project virtualenv;
- checked `systemctl --failed`;
- checked Hermes timer/service status.

Not performed:

- no `git reset`;
- no `git restore`;
- no `stash pop`;
- no unrelated deploy;
- no systemd service/timer changes;
- no source expansion;
- no candidates, evidence-grade records, artifacts, or downstream writes.

## Systemd

```text
official-sources-hermes-auditor.timer: active (waiting)
official-sources-hermes-auditor.service: inactive/dead after last successful run, status=0/SUCCESS
next timer trigger observed: 2026-06-05 00:15 UTC
```

## Follow-Up

After any documentation-only closeout commit is merged, fast-forward the VPS and update the
external contract to the new approved `origin/main` SHA before expecting the scheduled Hermes audit
to remain `GO`. Do not delete the preserved drift bundle or pop the stash during this release
window.

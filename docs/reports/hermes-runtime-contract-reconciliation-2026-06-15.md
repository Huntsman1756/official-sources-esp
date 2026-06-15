# Hermes Runtime Contract Reconciliation

Task: `TASK-OFFICIAL-SOURCES-HERMES-RUNTIME-CONTRACT-RECONCILIATION-001`

Date: 2026-06-15

## Scope

Recover the official-sources Hermes strict auditor after the scheduled service reported NO-GO due
to release-contract/runtime drift.

This task changed only:

- the checked-out runtime commit under `/opt/official-sources/app`;
- the external release contract at `/etc/official-sources/hermes-audit-contract.yaml`;
- systemd service state through a manual smoke of the existing auditor service.

It did not change source ingestion, SQLite data, candidates, evidence-grade records, downstream
writes, timers, service templates, caps, or model/runtime configuration.

## Preflight

Strict auditor failure observed before this task:

```text
VERDICT: NO-GO
expected_head_sha=1045bf794b8622d2f02213e70ec566628388a05d
actual_head_sha=bdddd07885bd203caab880cbbebd44db6e217102
remote_head_observed_sha=3fb4ad6f0a90d528355af87e5c4d7a1a521a7a03
failed_gate=observed checkout HEAD differs from expected release SHA
```

After fetching current remote state:

```text
actual=bdddd07885bd203caab880cbbebd44db6e217102
origin_main=1d5a20baae785f13c4800529d954d6e07f324e16
merge_base_actual_origin_main=1045bf794b8622d2f02213e70ec566628388a05d
main...origin/main [ahead 2, behind 7]
```

Runtime-only commits not on `origin/main`:

```text
bdddd07 docs(cli): record strict opposition export deployment
66116ca feat(cli): expose strict opposition alert export
```

`origin/main` commits not in the runtime checkout:

```text
1d5a20b docs(docm): record live snapshot backfill
3fb4ad6 fix(docm): persist monitor snapshot integrity
e21c26a fix(docm): add aid candidate dry run
f8a6703 fix(dogc): tighten aid candidate dry run
9974ca0 fix(boa): tighten aid candidate dry run
d02cf8e docs(boa): verify document URL mapping
8e7208e docs(boa): record metadata backfill catch-up
```

## Preservation

The divergent runtime HEAD was preserved before alignment:

```text
preserved_branch=preserve/vps-main-bdddd07-before-runtime-reconcile-20260615_044932
```

The external contract was backed up before editing:

```text
contract_backup=/etc/official-sources/hermes-audit-contract.yaml.before-runtime-reconcile-20260615_044932
```

## Runtime Alignment

The runtime checkout was aligned to `origin/main`:

```text
post_head=1d5a20baae785f13c4800529d954d6e07f324e16
git_status=main...origin/main
```

External contract after reconciliation:

```yaml
release:
  expected_head_sha: "1d5a20baae785f13c4800529d954d6e07f324e16"
  expected_branch: "main"
  approved_reason: "origin/main after DOCM live snapshot backfill documentation and integrity support"
  approved_at: "2026-06-15"
```

## Validation

SQLite validation stayed green:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=10 latest_version=10 status=valid
```

Direct strict audit:

```text
VERDICT: GO
expected_head_sha=1d5a20baae785f13c4800529d954d6e07f324e16
actual_head_sha=1d5a20baae785f13c4800529d954d6e07f324e16
remote_head_observed_sha=1d5a20baae785f13c4800529d954d6e07f324e16
git_worktree_clean=True
Failed gates: none
Warnings: none
Required human action: none
```

Systemd smoke:

```text
systemctl start official-sources-hermes-auditor.service
status=0/SUCCESS
strict_exit_code=0
report_path=/var/lib/hermes-official-sources-auditor/reports/vps-audit-20260615-044933.md
strict_report_path=/var/lib/hermes-official-sources-auditor/reports/strict-release-audit-20260615-044933.md
log_path=/var/lib/hermes-official-sources-auditor/logs/vps-audit-20260615-044933.log
```

Final failed units:

```text
systemctl --failed
0 loaded units listed
```

Final checkout:

```text
main...origin/main
```

## Result

Hermes strict release audit is back to GO on the official-sources VPS. The runtime now matches
current `origin/main`, the external contract matches the runtime, and the previous divergent
runtime branch remains preserved for later inspection if the opposition export branch needs to be
reintroduced through the normal release path.

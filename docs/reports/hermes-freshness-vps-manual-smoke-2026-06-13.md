# Hermes Freshness VPS Manual Smoke

Task: `TASK-HERMES-FRESHNESS-VPS-MANUAL-SMOKE-001`

Date: 2026-06-13

VPS: `mcpspain-official-sources-vps`

Runtime root: `/opt/official-sources/app`

State root: `/var/lib/hermes-official-sources-auditor`

## Verdict

```text
VPS manual smoke: GO
freshness report verdict: NO-GO
wrapper exit code: 0
strict audit after alignment: GO
systemd/timer activation: none
```

The smoke validates the intended report-only semantics:

```text
VERDICT: NO-GO means source freshness is not proven.
wrapper exit 0 means the report was generated correctly.
```

## Preflight

The VPS checkout was clean but behind `origin/main`.

```text
before HEAD: 506b68be0eff85f8023e53c630f4e41127ed985a
origin/main after fetch: 912b89fb88fc324456ce00809aa451de987a005b
merge base: 506b68be0eff85f8023e53c630f4e41127ed985a
worktree: clean
failed units: 0
```

The external strict-audit release contract also pointed at the old SHA:

```yaml
release:
  expected_head_sha: "506b68be0eff85f8023e53c630f4e41127ed985a"
  expected_branch: "main"
  approved_reason: "PR #35 downstream product contracts + PR #36 EduAyudas readiness docs"
  approved_at: "2026-06-11"
```

## Controlled VPS Alignment

The checkout was fast-forwarded only after confirming the worktree was clean and `origin/main`
matched the expected merge commit.

```text
git merge --ff-only origin/main
updated HEAD: 912b89fb88fc324456ce00809aa451de987a005b
```

The external release contract was updated to keep Hermes strict audit aligned:

```yaml
release:
  expected_head_sha: "912b89fb88fc324456ce00809aa451de987a005b"
  expected_branch: "main"
  approved_reason: "PR #37-#43 freshness report-only integration chain"
  approved_at: "2026-06-13"
```

No timer, service, systemd unit, SQLite database, registry file, downstream project, evidence,
candidate, publication artifact, or issue automation was changed.

## Smoke Command

```bash
cd /opt/official-sources/app

/opt/official-sources/app/.venv/bin/official-sources \
  hermes scheduled-freshness-report \
  --repo-root /opt/official-sources/app \
  --state-root /var/lib/hermes-official-sources-auditor \
  --official-sources-bin /opt/official-sources/app/.venv/bin/official-sources
```

The installed CLI exposed the expected command after alignment:

```text
{audit,scheduled-audit,scheduled-freshness-report,freshness-report}
```

## Smoke Result

```text
BEFORE_COUNT=0
report_path=/var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-20260613-174731.md
freshness_exit_code=0
WRAPPER_EXIT=0
AFTER_COUNT=1
```

New report:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports/hermes-freshness-report-20260613-174731.md
```

Report head:

```text
# Hermes Freshness Report

VERDICT: NO-GO
generated_at: 2026-06-13T17:47:31.405187Z
```

The `NO-GO` was expected because the current VPS runtime state does not yet contain freshness JSONL
for the critical expected sources:

```text
BDNS: missing, last_seen missing
BOCM: missing, last_seen missing
BOE: missing, last_seen missing
```

Forbidden-action flags in the report remained false:

```text
git_mutation: false
registry_mutated: false
sqlite_written: false
official_documents_written: false
evidence_created: false
candidates_created: false
artifacts_downloaded: false
downstream_writes: false
publication_created: false
systemd_mutated: false
```

## Post-Smoke State

```text
git status: ## main...origin/main
systemctl --failed: 0 loaded units listed
```

Strict audit after the controlled release alignment returned `GO`:

```text
VERDICT: GO
expected_head_sha: 912b89fb88fc324456ce00809aa451de987a005b
actual_head_sha: 912b89fb88fc324456ce00809aa451de987a005b
remote_head_observed_sha: 912b89fb88fc324456ce00809aa451de987a005b
git_worktree_clean: True
Failed gates: none
Warnings: none
STRICT_AUDIT_EXIT=0
```

## Not Done

```text
- no systemd timer created or activated
- no service modified or restarted
- no downstream smoke executed
- no SQLite write
- no ingest-monitor-date execution
- no registry mutation
- no official_documents/evidence/candidates/publication creation
- no automatic issue creation
```

## Next

The next task may define a systemd unit in report-only mode, but activation should remain separate:

```text
1. PR for unit/wrapper contract or manual service invocation.
2. Manual service smoke.
3. Timer activation only after review and another explicit approval.
```

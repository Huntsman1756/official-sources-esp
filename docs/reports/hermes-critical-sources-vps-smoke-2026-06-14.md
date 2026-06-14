# Hermes Critical Sources VPS Smoke - 2026-06-14

Task:

```text
TASK-HERMES-FRESHNESS-CRITICAL-SOURCES-VPS-SMOKE-001
```

## Purpose

Run the post-#54/#55 critical freshness smoke on the real VPS after aligning the checkout and the
external strict-audit contract.

Critical sources:

```text
BOE
BDNS
BOCM
```

## Scope

Allowed:

```text
- fast-forward the VPS checkout to merged main
- update the external strict-audit expected SHA
- run explicit source observations as official-sources
- write freshness runtime JSONL under the Hermes state root
- write latest-critical.jsonl under freshness-observations
- write one smoke report under freshness-reports
- run strict audit after the smoke
- inspect systemctl --failed
```

Forbidden and not performed:

```text
- scheduler activation
- systemd/timer creation or modification
- SQLite writes
- ingest-bdns-*
- ingest-monitor-date
- registry mutation
- official_documents/evidence/candidates/publication
- product/external project writes
- automatic issues
```

## VPS Alignment

VPS:

```text
mcpspain-official-sources-vps
app_root=/opt/official-sources/app
state_root=/var/lib/hermes-official-sources-auditor
```

Checkout alignment:

```text
BEFORE_HEAD=c311330812ce25443c82f07089dc421d96eb062d
AFTER_HEAD=afc4d3781838b58cb6a1ed9af873e6574cc62590
origin/main=afc4d3781838b58cb6a1ed9af873e6574cc62590
```

External strict-audit contract:

```text
path=/etc/official-sources/hermes-audit-contract.yaml
expected_head_sha=afc4d3781838b58cb6a1ed9af873e6574cc62590
approved_reason="PR #55 critical freshness local smoke and RFC2822 record-date fix"
```

An initial manual contract edit used an incorrect hand-typed SHA prefix. This was corrected before
running strict audit:

```text
corrected_contract_sha=afc4d3781838b58cb6a1ed9af873e6574cc62590
```

## Permission Finding

The first VPS freshness report attempt printed a valid report but failed while writing the markdown:

```text
PermissionError: [Errno 13] Permission denied:
/var/lib/hermes-official-sources-auditor/freshness-reports/critical-sources-smoke-20260614-041837.md
```

Inspection:

```text
/var/lib/hermes-official-sources-auditor: official-sources:official-sources 750
/var/lib/hermes-official-sources-auditor/freshness-runtime: official-sources:official-sources 775
/var/lib/hermes-official-sources-auditor/freshness-observations: official-sources:official-sources 775
/var/lib/hermes-official-sources-auditor/freshness-reports: root:root 755
```

Narrow fix applied:

```bash
chown official-sources:official-sources \
  /var/lib/hermes-official-sources-auditor/freshness-reports
```

Result:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports: official-sources:official-sources 755
```

No systemd units or timers were changed.

## Commands

BOE RSS observation:

```bash
sudo -u official-sources -H /opt/official-sources/app/.venv/bin/official-sources \
  rss monitor \
  --source BOE \
  --date 2026-06-14 \
  --limit 1 \
  --write \
  --output-root /var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor
```

BOCM RSS observation:

```bash
sudo -u official-sources -H /opt/official-sources/app/.venv/bin/official-sources \
  hermes bocm-rss-observation \
  --repo-root /opt/official-sources/app \
  --state-root /var/lib/hermes-official-sources-auditor \
  --official-sources-bin /opt/official-sources/app/.venv/bin/official-sources \
  --date today \
  --limit 1
```

BDNS observation:

```bash
sudo -u official-sources -H /opt/official-sources/app/.venv/bin/official-sources \
  hermes bdns-observation \
  --repo-root /opt/official-sources/app \
  --state-root /var/lib/hermes-official-sources-auditor \
  --official-sources-bin /opt/official-sources/app/.venv/bin/official-sources \
  --limit 1
```

Observation compaction:

```bash
sudo -u official-sources -H /opt/official-sources/app/.venv/bin/official-sources \
  hermes freshness-observations \
  --runtime-root /var/lib/hermes-official-sources-auditor/freshness-runtime \
  --source BOE \
  --source BDNS \
  --source BOCM \
  --output /var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl
```

Freshness report:

```bash
sudo -u official-sources -H /opt/official-sources/app/.venv/bin/official-sources \
  hermes freshness-report \
  --observations-jsonl /var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl \
  --now 2026-06-14T04:19:13Z \
  --critical-source BOE \
  --critical-source BDNS \
  --critical-source BOCM \
  --expected-source BOE \
  --expected-source BDNS \
  --expected-source BOCM \
  --output /var/lib/hermes-official-sources-auditor/freshness-reports/critical-sources-smoke-20260614-041913.md
```

## Observation Outputs

```text
BOE_RSS_EXIT=0
BOCM_WRAPPER_EXIT=0
BDNS_WRAPPER_EXIT=0
OBSERVATIONS_EXIT=0
observations_written=3
```

Observation JSONL:

```text
/var/lib/hermes-official-sources-auditor/freshness-observations/latest-critical.jsonl
owner=official-sources:official-sources
mode=664
size=1294
```

Report:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports/critical-sources-smoke-20260614-041913.md
owner=official-sources:official-sources
mode=664
size=1619
```

## Freshness Result

```text
VERDICT: GO
REPORT_EXIT=0
```

Sources:

```text
BDNS healthy
  last_seen=2026-06-14T04:18:39.757789Z
  latest_record_date=2026-06-14T00:00:00Z
  input_kind=api_monitor_jsonl
  reason=derived from operator-controlled BDNS latest API observation

BOCM healthy
  last_seen=2026-06-14T00:00:00Z
  latest_record_date=2026-06-13T00:00:00Z
  input_kind=rss_monitor_jsonl
  reason=derived from monitor discovered_at

BOE healthy
  last_seen=2026-06-14T00:00:00Z
  latest_record_date=2026-06-12T22:00:00Z
  input_kind=rss_monitor_jsonl
  reason=derived from monitor discovered_at
```

Freshness failed gates:

```text
none
```

Freshness warnings:

```text
none
```

Forbidden-action flags:

```text
git_mutation=false
registry_mutated=false
sqlite_written=false
official_documents_written=false
evidence_created=false
candidates_created=false
artifacts_downloaded=false
downstream_writes=false
publication_created=false
systemd_mutated=false
```

## Post-Smoke Strict Audit

```text
STRICT_AUDIT_EXIT=0
VERDICT: GO
expected_head_sha=afc4d3781838b58cb6a1ed9af873e6574cc62590
actual_head_sha=afc4d3781838b58cb6a1ed9af873e6574cc62590
remote_head_observed_sha=afc4d3781838b58cb6a1ed9af873e6574cc62590
git_worktree_clean=True
failed_gates=none
warnings=none
```

## System State

```text
systemctl --failed: 0 loaded units listed
SYSTEMCTL_FAILED_EXIT=0
git status --porcelain count=0
```

## Operational Verdict

```text
VPS critical freshness smoke: GO
BOE: healthy
BDNS: healthy
BOCM: healthy
strict audit after smoke: GO
systemctl --failed: 0
worktree: clean
scheduler: still not activated
```

The system is now ready for a separate report-only schedule integration task. That next task should
still avoid auto-fix, source promotion, SQLite writes, downstream writes, and publication.

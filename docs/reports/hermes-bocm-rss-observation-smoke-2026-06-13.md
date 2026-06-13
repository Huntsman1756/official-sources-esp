# Hermes BOCM RSS Observation Smoke - 2026-06-13

Status: completed

Task:

```text
TASK-HERMES-FRESHNESS-BOCM-RSS-OBSERVATION-SMOKE-001
```

Related PR:

```text
PR #52: feat(hermes): add BOCM RSS freshness observation
```

## Purpose

Validate the merged BOCM RSS freshness observation wrapper locally and on the VPS before any
scheduler or systemd integration.

The wrapper is:

```text
official-sources hermes bocm-rss-observation
```

It writes BOCM RSS monitor JSONL under `freshness-runtime` and then writes BOCM freshness
observation JSONL under `freshness-observations`.

## Scope

Allowed:

```text
- merge PR #52
- fast-forward VPS checkout to merged main
- align external strict-audit contract to merged main
- run bocm-rss-observation manually
- write BOCM observation state under the selected state-root
- run freshness-report against latest-bocm-rss.jsonl
- run strict audit after the smoke
```

Forbidden:

```text
- scheduler activation
- systemd/timer creation or modification
- service restart
- SQLite writes
- registry mutation
- ingest-monitor-date
- ingest-bocm-date
- BDNS changes
- official_documents/evidence/candidates/publication
- product/external project writes
- automatic issues
```

## Merge State

PR #52 was merged and local `main` fast-forwarded to:

```text
c311330 Merge pull request #52 from Huntsman1756/codex/task-hermes-freshness-bocm-rss-observation-001
```

The VPS checkout was fast-forwarded:

```text
before: 6b689a7
after:  c311330812ce25443c82f07089dc421d96eb062d
```

The external strict-audit contract was updated to:

```text
expected_head_sha: "c311330812ce25443c82f07089dc421d96eb062d"
approved_reason: "PR #52 BOCM RSS freshness observation smoke"
```

## Local Smoke

Command shape:

```powershell
.venv\Scripts\official-sources.exe hermes bocm-rss-observation `
  --repo-root G:\_Proyectos\mcpspain\official-sources `
  --state-root $env:TEMP\hermes-bocm-rss-observation-smoke-20260613-221920 `
  --official-sources-bin G:\_Proyectos\mcpspain\official-sources\.venv\Scripts\official-sources.exe `
  --date today `
  --limit 1
```

Observed:

```text
bocm_rss_observation_exit_code=0
EXIT_CODE=0
```

Generated files:

```text
C:\Users\rome_\AppData\Local\Temp\hermes-bocm-rss-observation-smoke-20260613-221920\freshness-runtime\data\rss_monitor\BOCM\2026-06-13\rss_discovery.jsonl
C:\Users\rome_\AppData\Local\Temp\hermes-bocm-rss-observation-smoke-20260613-221920\freshness-observations\latest-bocm-rss.jsonl
```

Observation JSONL:

```json
{"confidence": "operational", "input_kind": "rss_monitor_jsonl", "input_path": "C:\\Users\\rome_\\AppData\\Local\\Temp\\hermes-bocm-rss-observation-smoke-20260613-221920\\freshness-runtime\\data\\rss_monitor\\BOCM\\2026-06-13\\rss_discovery.jsonl", "latest_record_date": "2026-06-13T00:00:00Z", "observation_kind": "existing_runtime_state", "observed_at": "2026-06-13T00:00:00Z", "reason": "derived from monitor discovered_at; no live fetch", "source": "BOCM", "timestamp_type": "observed"}
```

The `reason` field is emitted by `freshness-observations` and means the producer read existing
runtime JSONL without fetching. The wrapper itself did run the BOCM RSS monitor immediately before
that producer step.

Timestamp semantics:

```text
observed_at comes from the monitor-emitted discovered_at field.
rss_monitor emits discovered_at as <target_date>T00:00:00Z for the requested monitor date.
published_at remains a separate RSS record field and is not used as freshness observed_at.
latest_record_date is diagnostic only.
```

Freshness report over the observation JSONL:

```text
VERDICT: GO
generated_at: 2026-06-13T20:19:31Z
BOCM: healthy, last_seen=2026-06-13T00:00:00Z, threshold=72h, age=20.3h
REPORT_EXIT=0
```

Local checkout after smoke:

```text
git status --short: clean
```

## VPS Smoke

VPS:

```text
host: 157.90.22.40
alias: mcpspain-official-sources-vps
checkout: /opt/official-sources/app
state-root: /var/lib/hermes-official-sources-auditor
```

The state root is owned by the service user:

```text
official-sources:official-sources 750 /var/lib/hermes-official-sources-auditor
```

The smoke command was executed as `official-sources`, not as root:

```bash
sudo -u official-sources -H /opt/official-sources/app/.venv/bin/official-sources \
  hermes bocm-rss-observation \
  --repo-root /opt/official-sources/app \
  --state-root /var/lib/hermes-official-sources-auditor \
  --official-sources-bin /opt/official-sources/app/.venv/bin/official-sources \
  --date today \
  --limit 1
```

Observed:

```text
rss_output_path=/var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor/BOCM/2026-06-13/rss_discovery.jsonl
observations_path=/var/lib/hermes-official-sources-auditor/freshness-observations/latest-bocm-rss.jsonl
bocm_rss_observation_exit_code=0
WRAPPER_EXIT=0
```

Generated file ownership:

```text
official-sources:official-sources 664 12364 /var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor/BOCM/2026-06-13/rss_discovery.jsonl
official-sources:official-sources 664   436 /var/lib/hermes-official-sources-auditor/freshness-observations/latest-bocm-rss.jsonl
```

Observation JSONL:

```json
{"confidence": "operational", "input_kind": "rss_monitor_jsonl", "input_path": "/var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor/BOCM/2026-06-13/rss_discovery.jsonl", "latest_record_date": "2026-06-13T00:00:00Z", "observation_kind": "existing_runtime_state", "observed_at": "2026-06-13T00:00:00Z", "reason": "derived from monitor discovered_at; no live fetch", "source": "BOCM", "timestamp_type": "observed"}
```

As in the local smoke, `no live fetch` applies to the observation producer step, not to the wrapper
as a whole. The wrapper intentionally ran the BOCM RSS monitor as the manual observation action.

Timestamp semantics:

```text
observed_at comes from the monitor-emitted discovered_at field.
rss_monitor emits discovered_at as <target_date>T00:00:00Z for the requested monitor date.
published_at remains a separate RSS record field and is not used as freshness observed_at.
latest_record_date is diagnostic only.
```

Freshness report over the VPS observation JSONL:

```text
VERDICT: GO
generated_at: 2026-06-13T20:20:36Z
BOCM: healthy, last_seen=2026-06-13T00:00:00Z, threshold=72h, age=20.3h
REPORT_EXIT=0
```

The freshness report confirmed forbidden-action flags:

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

## Post-Smoke Strict Audit

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources hermes audit \
  --repo-root /opt/official-sources/app \
  --registry /opt/official-sources/app/config/sources.yaml \
  --project-state /opt/official-sources/app/PROJECT_STATE.md \
  --release-contract /etc/official-sources/hermes-audit-contract.yaml \
  --strict-release-contract \
  --fail-on-no-go
```

Result:

```text
VERDICT: GO
expected_head_sha: c311330812ce25443c82f07089dc421d96eb062d
actual_head_sha: c311330812ce25443c82f07089dc421d96eb062d
remote_head_observed_sha: c311330812ce25443c82f07089dc421d96eb062d
git_worktree_clean: True
failed gates: none
warnings: none
```

System state:

```text
systemctl --failed: 0 loaded units listed
git status: ## main...origin/main
```

## Conclusion

```text
PR #52 merged: yes
local BOCM RSS observation smoke: GO
VPS BOCM RSS observation smoke: GO
BOCM freshness from observation JSONL: GO
strict audit after smoke: GO
systemctl --failed: 0
scheduler activation: still NO-GO
BDNS observation path: still unresolved
```

BOCM now has a proven manual observation path using RSS monitor JSONL in Hermes state. This does not
make the global freshness schedule ready: `BDNS` still needs an approved observation-only path or an
explicit operator-owned refresh cadence.

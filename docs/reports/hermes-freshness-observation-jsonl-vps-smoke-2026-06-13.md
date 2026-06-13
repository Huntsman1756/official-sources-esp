# Hermes Freshness Observation JSONL VPS Smoke - 2026-06-13

Status: completed

Task:

```text
TASK-HERMES-FRESHNESS-OBSERVATION-JSONL-VPS-SMOKE-001
```

Related PR:

```text
PR #48: feat(hermes): consume freshness observation jsonl
```

## Purpose

Validate the full post-merge VPS chain:

```text
existing runtime state -> freshness-observations JSONL -> freshness-report --observations-jsonl
```

This smoke verifies the corrected runtime database path and confirms the current critical-source
freshness state without activating any scheduler.

## Scope

Allowed:

```text
- fast-forward VPS checkout to merged main
- align external strict-audit release contract to the merged SHA
- run freshness-observations manually
- write smoke files only under /tmp
- run freshness-report manually against the generated JSONL
- run strict audit after the smoke
```

Forbidden:

```text
- scheduler activation
- systemd/timer changes
- live fetches
- ingest-monitor-date
- SQLite writes
- registry mutation
- official_documents/evidence/candidates creation
- product/downstream writes
- automatic issues
```

## VPS Alignment

VPS:

```text
host: 157.90.22.40
alias: mcpspain-official-sources-vps
checkout: /opt/official-sources/app
```

Before alignment:

```text
HEAD: 69762bf
systemctl --failed: 0 loaded units listed
```

The VPS checkout was fast-forwarded to merged main:

```text
69762bf..6b689a7
```

The external strict-audit contract was updated to:

```text
expected_head_sha: 6b689a72b0b313192639af32a1facec538ada495
approved_reason: PR #48 freshness observation JSONL consumption
```

## Correct Runtime Database

The freshness observation producer must use the real service database:

```text
/opt/official-sources/data/official_sources.sqlite
```

It must not use the checkout-local SQLite:

```text
/opt/official-sources/app/official-sources.sqlite
```

The earlier smoke that used the checkout-local SQLite correctly failed closed, but it did not
represent the active service state.

## Smoke Command

```bash
cd /opt/official-sources/app

SMOKE_ROOT=/tmp/hermes-observation-jsonl-smoke-20260613-2148
mkdir -p "$SMOKE_ROOT"
OBS="$SMOKE_ROOT/freshness-observations.jsonl"
REPORT="$SMOKE_ROOT/freshness-report.md"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

/opt/official-sources/app/.venv/bin/official-sources \
  hermes freshness-observations \
  --runtime-root /opt/official-sources/app \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --source BOE \
  --source BDNS \
  --source BOCM \
  --output "$OBS"

/opt/official-sources/app/.venv/bin/official-sources \
  hermes freshness-report \
  --observations-jsonl "$OBS" \
  --now "$NOW" \
  --default-threshold-hours 72 \
  --critical-source BOE \
  --critical-source BDNS \
  --critical-source BOCM \
  --expected-source BOE \
  --expected-source BDNS \
  --expected-source BOCM \
  --output "$REPORT"
```

Observed:

```text
NOW=2026-06-13T19:41:11Z
OBS_EXISTS=true
REPORT_EXISTS=true
PRODUCER_EXIT=0
REPORT_EXIT=0
OBS_LINES=3
```

## Freshness Result

Report verdict:

```text
VERDICT: NO-GO
generated_at: 2026-06-13T19:41:11Z
```

Checks:

```text
BDNS | stale  | last_seen=2026-05-31T13:47:15.960144Z | threshold=72h | age=317.9h
BOCM | stale  | last_seen=2026-05-21T20:19:13.900362Z | threshold=72h | age=551.4h
BOE  | healthy| last_seen=2026-06-13T07:41:10.656169Z | threshold=72h | age=12.0h
```

Failed gates:

```text
BDNS critical stale for 317.9h over threshold 72h
BOCM critical stale for 551.4h over threshold 72h
```

Forbidden actions confirmed by the report:

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
expected_head_sha: 6b689a72b0b313192639af32a1facec538ada495
actual_head_sha: 6b689a72b0b313192639af32a1facec538ada495
remote_head_observed_sha: 6b689a72b0b313192639af32a1facec538ada495
git_worktree_clean: True
failed gates: none
warnings: none
```

Post-smoke system state:

```text
git status: ## main...origin/main
systemctl --failed: 0 loaded units listed
```

## Conclusion

```text
observation producer: GO
observation JSONL consumption: GO
BOE freshness: healthy
BDNS freshness: stale
BOCM freshness: stale
freshness verdict: NO-GO
scheduler activation: still NO-GO
```

The freshness system now has a real signal:

```text
before: critical observations appeared missing because the wrong SQLite path was inspected
now: BOE is healthy, while BDNS and BOCM are stale
```

The next useful task is to investigate why `BDNS` and `BOCM` have not produced fresh observations
since May. Activating a timer now would generate a correct but expected daily `NO-GO`.

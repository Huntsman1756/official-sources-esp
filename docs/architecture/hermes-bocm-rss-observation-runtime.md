# Hermes BOCM RSS Observation Runtime

Status: implemented as explicit manual wrapper

Task:

```text
TASK-HERMES-FRESHNESS-BOCM-RSS-OBSERVATION-001
```

## Purpose

`official-sources hermes bocm-rss-observation` creates a BOCM freshness observation from the
existing RSS monitor path without activating any scheduler.

It performs two explicit steps:

```text
1. Run BOCM RSS monitor with --write into Hermes freshness runtime state.
2. Run freshness-observations over that runtime state and write BOCM observation JSONL.
```

The command is manual/operator-invoked. It is not a timer and it is not a source repair loop.

## Command

```bash
official-sources hermes bocm-rss-observation \
  --repo-root /opt/official-sources/app \
  --state-root /var/lib/hermes-official-sources-auditor \
  --official-sources-bin /opt/official-sources/app/.venv/bin/official-sources \
  --date today \
  --limit 1
```

## Write Surface

The command writes only under the selected Hermes state root:

```text
<state-root>/freshness-runtime/data/rss_monitor/BOCM/<YYYY-MM-DD>/rss_discovery.jsonl
<state-root>/freshness-observations/latest-bocm-rss.jsonl
```

It does not write into the audited checkout by default.

Default VPS paths:

```text
state-root: /var/lib/hermes-official-sources-auditor
runtime root: /var/lib/hermes-official-sources-auditor/freshness-runtime
RSS JSONL: /var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor/BOCM/<YYYY-MM-DD>/rss_discovery.jsonl
observation JSONL: /var/lib/hermes-official-sources-auditor/freshness-observations/latest-bocm-rss.jsonl
```

## Timestamp Semantics

The resulting freshness observation uses the RSS monitor operational timestamp:

```text
observed_at = discovered_at or observed_at from rss_discovery.jsonl
```

RSS `published_at` / `updated_at` remain record-date diagnostics. They do not become freshness
timestamps.

## Failure Semantics

The wrapper fails with a non-zero exit when:

```text
- required state directories cannot be created
- BOCM RSS monitor exits non-zero
- BOCM RSS monitor exits 0 but does not write the expected JSONL
- freshness-observations exits non-zero
- freshness-observations exits 0 but does not write the observation JSONL
```

A failed run does not delete or overwrite previous unrelated observations.

## Boundaries

Allowed:

```text
- execute existing BOCM RSS monitor for one source
- write BOCM RSS JSONL under freshness-runtime
- write BOCM observation JSONL under freshness-observations
- return operational failure when expected outputs are missing
```

Forbidden:

```text
- scheduler activation
- systemd/timer creation or modification
- SQLite writes
- registry mutation
- ingest-monitor-date
- ingest-bocm-date
- official_documents/evidence/candidates/publication
- product/external project writes
- automatic issues or fixes
```

## Scheduler Status

Scheduler activation remains blocked after this command.

Reason:

```text
BOCM now has a manual observation path, but BDNS still needs either:
- a current operator-owned ingestion_run cadence, or
- a future observation-only producer.
```

The next required step is a local/VPS smoke of this manual wrapper. A timer should not be added in
the same PR.

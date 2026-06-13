# Hermes Freshness Observation Producer

Status: implemented as explicit operator command

Task:

```text
TASK-HERMES-FRESHNESS-OBSERVATION-PRODUCER-001
```

## Purpose

`official-sources hermes freshness-observations` produces a JSONL file of operational freshness
observations from state that already exists locally.

It does not fetch sources, execute ingestion, activate a timer, or mutate runtime data. Its only
write surface is the JSONL path passed with `--output`.

## Command

```bash
official-sources hermes freshness-observations \
  --runtime-root /opt/official-sources/app \
  --db-path /opt/official-sources/app/official-sources.sqlite \
  --source BOE \
  --source BDNS \
  --source BOCM \
  --output /var/lib/hermes-official-sources-auditor/freshness-observations/latest.jsonl
```

`--db-path` is optional. When it is provided, the database is opened read-only and only
`ingestion_runs` are inspected.

## Inputs

The producer reads:

```text
<runtime-root>/data/rss_monitor/*/*/rss_discovery.jsonl
<runtime-root>/data/api_monitor/*/*/api_discovery.jsonl
<runtime-root>/data/html_monitor/*/*/html_discovery.jsonl
```

For monitor JSONL, `observed_at` is derived only from monitor observation fields:

```text
discovered_at
observed_at
```

Official record dates such as `published_at` and `updated_at` may be emitted as
`latest_record_date`, but they are diagnostic only. They do not become `observed_at`.

When `--db-path` is provided, the producer reads successful or controlled no-publication
`ingestion_runs`:

```sql
status IN ('success', 'no_publication')
finished_at IS NOT NULL
```

The SQLite timestamp source is `finished_at`, because it proves an existing local runtime run
completed. Failed and pending runs are ignored as freshness observations.

## Output Shape

Each JSONL row is an observation:

```json
{
  "source": "BOE",
  "observed_at": "2026-06-13T07:30:00Z",
  "observation_kind": "existing_runtime_state",
  "input_path": "data/rss_monitor/BOE/2026-06-13/rss_discovery.jsonl",
  "input_kind": "rss_monitor_jsonl",
  "timestamp_type": "observed",
  "confidence": "operational",
  "reason": "derived from monitor discovered_at; no live fetch",
  "latest_record_date": "2026-06-13T07:00:00Z"
}
```

The producer keeps the latest observation per source across the available inputs.

## Boundaries

Allowed:

```text
- read existing monitor JSONL
- read existing SQLite ingestion_runs with a read-only connection
- write the explicit output JSONL
- filter sources with --source
```

Forbidden:

```text
- live fetches
- scheduler activation
- systemd/timer changes
- SQLite writes
- ingest-monitor-date
- registry mutation
- official_documents/evidence/candidates creation
- product/downstream writes
- automatic fixes or issues
```

## Follow-Up

The scheduler remains blocked until either:

```text
1. BOE, BDNS, and BOCM have real observations available to consume.
2. A daily missing-input NO-GO is explicitly accepted as operationally useful.
```

The preferred next step is a smoke of the producer against local/main and then VPS state, still
without activating any schedule.

## Report Consumption

Freshness reports can consume the generated observation JSONL directly:

```bash
official-sources hermes freshness-report \
  --observations-jsonl /var/lib/hermes-official-sources-auditor/freshness-observations/latest.jsonl \
  --now 2026-06-13T20:40:00Z \
  --default-threshold-hours 72 \
  --critical-source BOE \
  --critical-source BDNS \
  --critical-source BOCM \
  --expected-source BOE \
  --expected-source BDNS \
  --expected-source BOCM
```

This input is read-only. It does not run the producer, perform live fetches, write SQLite, or
activate a scheduler.

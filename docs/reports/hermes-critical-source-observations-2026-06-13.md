# Hermes Critical Source Observations - 2026-06-13

Status: completed

Task:

```text
TASK-HERMES-FRESHNESS-CRITICAL-SOURCE-OBSERVATIONS-001
```

## Purpose

Prove whether `BOE`, `BDNS`, and `BOCM` have real operational freshness observations available
from existing runtime state, without live fetches and without inventing timestamps.

## Scope

Allowed:

```text
- read existing VPS runtime state
- read existing SQLite ingestion_runs through the freshness observation producer
- write one explicit smoke JSONL under /tmp
- consume the JSONL with freshness-report
- document the result
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

## Finding: Previous Smoke Used The Wrong DB

The previous producer smoke used:

```text
/opt/official-sources/app/official-sources.sqlite
```

That checkout-local SQLite is not the database used by the systemd BOE daily service.

The real service state is under:

```text
/opt/official-sources/data/official_sources.sqlite
```

Evidence:

```text
/opt/official-sources/data/official_sources.sqlite size: 104718336 bytes
/opt/official-sources/app/official-sources.sqlite size: 155648 bytes
```

The systemd BOE daily service also proves the real runtime path is active. Latest visible run:

```text
Jun 13 07:30:18 official-sources ingest-boe-summary source_code=BOE target_date=2026-06-13
status=success documents_fetched=326 documents_new=326 documents_updated=0 last_http_status=200
Jun 13 07:41:11 status source_code=BOE target_date=2026-06-13
ingestion_status=success documents=326 xml_files=326 html_files=326 failed_downloads=0
```

## Existing Runtime Runs

Read-only query against:

```text
/opt/official-sources/data/official_sources.sqlite
```

Result:

```text
BDNS success: 19, latest_finished_at=2026-05-31T13:47:15.960144+00:00
BOCM failed: 5, latest_finished_at=2026-05-21T20:49:16.593666+00:00
BOCM no_publication: 2, latest_finished_at=2026-05-21T20:18:55.503394+00:00
BOCM success: 13, latest_finished_at=2026-05-21T20:19:13.900362+00:00
BOE failed: 2, latest_finished_at=2026-05-20T04:41:40.150102+00:00
BOE no_publication: 29, latest_finished_at=2026-06-07T07:30:07.468296+00:00
BOE partial: 9, latest_finished_at=2026-06-05T07:36:53.860497+00:00
BOE success: 201, latest_finished_at=2026-06-13T07:41:10.656169+00:00
```

## Producer Smoke

Command:

```bash
cd /opt/official-sources/app

SMOKE_ROOT=/tmp/hermes-critical-source-observations-20260613-2035
mkdir -p "$SMOKE_ROOT"
OUTPUT="$SMOKE_ROOT/freshness-observations.jsonl"

/opt/official-sources/app/.venv/bin/official-sources \
  hermes freshness-observations \
  --runtime-root /opt/official-sources/app \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --source BOE \
  --source BDNS \
  --source BOCM \
  --output "$OUTPUT"
```

Observed:

```text
observations_written=3
OUTPUT_EXISTS=true
EXIT_CODE=0
```

Output JSONL:

```jsonl
{"confidence": "operational", "input_kind": "sqlite_ingestion_runs", "input_path": "/opt/official-sources/data/official_sources.sqlite", "observation_kind": "existing_runtime_state", "observed_at": "2026-05-31T13:47:15.960144Z", "reason": "derived from successful ingestion_run id=417 status=success; no live fetch", "source": "BDNS", "timestamp_type": "observed"}
{"confidence": "operational", "input_kind": "sqlite_ingestion_runs", "input_path": "/opt/official-sources/data/official_sources.sqlite", "observation_kind": "existing_runtime_state", "observed_at": "2026-05-21T20:19:13.900362Z", "reason": "derived from successful ingestion_run id=248 status=success; no live fetch", "source": "BOCM", "timestamp_type": "observed"}
{"confidence": "operational", "input_kind": "sqlite_ingestion_runs", "input_path": "/opt/official-sources/data/official_sources.sqlite", "observation_kind": "existing_runtime_state", "observed_at": "2026-06-13T07:41:10.656169Z", "reason": "derived from successful ingestion_run id=471 status=success; no live fetch", "source": "BOE", "timestamp_type": "observed"}
```

## Freshness Report From Observation JSONL

The VPS JSONL was copied locally and consumed with the new read-only input:

```powershell
.\.venv\Scripts\official-sources.exe hermes freshness-report `
  --observations-jsonl $localSmoke `
  --now 2026-06-13T20:40:00Z `
  --default-threshold-hours 72 `
  --critical-source BOE `
  --critical-source BDNS `
  --critical-source BOCM `
  --expected-source BOE `
  --expected-source BDNS `
  --expected-source BOCM
```

Result:

```text
VERDICT: NO-GO

BDNS: stale, last_seen=2026-05-31T13:47:15.960144Z, age_hours=318.9
BOCM: stale, last_seen=2026-05-21T20:19:13.900362Z, age_hours=552.3
BOE: healthy, last_seen=2026-06-13T07:41:10.656169Z, age_hours=13.0
```

Failed gates:

```text
BDNS critical stale for 318.9h over threshold 72h
BOCM critical stale for 552.3h over threshold 72h
```

## Conclusion

```text
BOE observation: real and healthy
BDNS observation: real but stale
BOCM observation: real but stale
missing-input diagnosis: closed
freshness verdict: still NO-GO
scheduler activation: still NO-GO
```

The system now has real operational `last_seen` values for all three critical sources when the
producer uses the real runtime SQLite path.

The blocker has changed:

```text
before: BOE/BDNS/BOCM observations missing
now: BDNS and BOCM observations are stale
```

Do not activate a scheduler until the stale BDNS and BOCM observation paths are intentionally
refreshed or accepted as a daily `NO-GO` signal.

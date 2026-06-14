# Hermes BDNS Observation Runtime

Status: implemented as explicit manual wrapper

Task:

```text
TASK-HERMES-FRESHNESS-BDNS-OBSERVATION-ONLY-001
```

## Purpose

`official-sources hermes bdns-observation` creates a BDNS freshness observation from a bounded
latest-convocatorias API check without running BDNS ingestion or activating any scheduler.

It performs two explicit steps:

```text
1. Fetch BDNS latest convocatorias with a small limit and write API monitor JSONL into Hermes
   freshness runtime state.
2. Run freshness-observations over that runtime state and write BDNS observation JSONL.
```

The command is manual/operator-invoked. It is not a timer and it is not a source repair loop.

## Command

```bash
official-sources hermes bdns-observation \
  --repo-root /opt/official-sources/app \
  --state-root /var/lib/hermes-official-sources-auditor \
  --official-sources-bin /opt/official-sources/app/.venv/bin/official-sources \
  --limit 1
```

## Write Surface

The command writes only under the selected Hermes state root:

```text
<state-root>/freshness-runtime/data/api_monitor/BDNS/<YYYY-MM-DD>/api_discovery.jsonl
<state-root>/freshness-observations/latest-bdns.jsonl
```

It does not write into the audited checkout by default.

Default VPS paths:

```text
state-root: /var/lib/hermes-official-sources-auditor
runtime root: /var/lib/hermes-official-sources-auditor/freshness-runtime
API JSONL: /var/lib/hermes-official-sources-auditor/freshness-runtime/data/api_monitor/BDNS/<YYYY-MM-DD>/api_discovery.jsonl
observation JSONL: /var/lib/hermes-official-sources-auditor/freshness-observations/latest-bdns.jsonl
```

## Timestamp Semantics

The resulting freshness observation uses the command execution timestamp:

```text
observed_at = discovered_at emitted by bdns-observation when the bounded API response is fetched
```

BDNS `fechaPublicacion` is emitted only as `published_at` in the API monitor JSONL. The downstream
freshness-observations producer may surface it as `latest_record_date` diagnostic metadata, but it
must not become `observed_at`.

## Failure Semantics

The wrapper fails with a non-zero exit when:

```text
- required state directories cannot be created
- BDNS latest API fetch fails
- BDNS latest payload cannot be parsed
- BDNS latest payload contains zero usable records
- freshness-observations exits non-zero
- freshness-observations exits 0 but does not write the observation JSONL
```

A failed run does not delete previous unrelated observations.

## Boundaries

Allowed:

```text
- execute one bounded BDNS latest API observation
- write BDNS API JSONL under freshness-runtime
- write BDNS observation JSONL under freshness-observations
- return operational failure when expected outputs are missing
```

Forbidden:

```text
- scheduler activation
- systemd/timer creation or modification
- ingest-bdns-latest
- ingest-bdns-call
- ingest-bdns-catalog
- ingest-bdns-concesiones
- SQLite writes
- registry mutation
- official_documents/evidence/candidates/publication
- product/external project writes
- automatic issues or fixes
```

## Scheduler Status

Scheduler activation remains blocked after this command until local and VPS smokes prove:

```text
- BDNS observation JSONL is generated under the real Hermes state root
- freshness-report consumes BDNS, BOE, and BOCM observations together
- strict audit remains GO after the manual smoke
- NO-GO remains report content, not an auto-fix trigger
```

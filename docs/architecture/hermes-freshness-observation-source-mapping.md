# Hermes Freshness Observation Source Mapping

Task: `TASK-HERMES-FRESHNESS-OBSERVATION-SOURCE-MAPPING-001`

Status: mapping-only

Date: 2026-06-13

## Verdict

The freshness wrapper and VPS report path are working, but the critical sources do not yet have
usable runtime observations in the current VPS state.

```text
freshness engine: ready
scheduled wrapper: ready
critical last_seen inputs: missing
scheduler activation: not ready
```

This document maps the intended `last_seen` source for `BOE`, `BDNS`, and `BOCM` before any timer or
daily scheduler is activated.

## Evidence Inspected

Local repository inspection:

```text
BOE registry: validated API, XML, HTML, RSS; monitor_support=available
BDNS registry: validated API and HTML; monitor_support=available
BOCM registry: validated RSS; paused HTML/XML adapter paths; monitor_support=available
data/*_monitor/*/*_discovery.jsonl: absent for BOE, BDNS, and BOCM
```

VPS read-only inspection after PR #43 and PR #44:

```text
runtime root: /opt/official-sources/app
SQLite path: /opt/official-sources/app/official-sources.sqlite
data monitor JSONL files: none
BOE ingestion_runs: none
BDNS ingestion_runs: none
BOCM ingestion_runs: none
BOE official_documents: 0
BDNS official_documents: 0
BOCM official_documents: 0
```

Current freshness report result on VPS:

```text
BOE: missing
BDNS: missing
BOCM: missing
VERDICT: NO-GO
wrapper exit: 0
```

That `NO-GO` is correct. The report cannot prove freshness because no acceptable `last_seen` input
exists yet.

## Timestamp Semantics

Freshness needs an operational observation timestamp:

```text
last_seen = when official-sources observed a source through a controlled runtime path
```

It must not silently use an official publication date as operational freshness. Publication dates
can be reported as `latest_record_date`, but they do not prove that the local system observed the
source recently.

Accepted timestamp classes:

```text
observed:
  - monitor JSONL discovered_at
  - successful adapter ingestion_runs.finished_at
  - controlled no_publication ingestion_runs.finished_at

record_date_only:
  - RSS/API/HTML published_at
  - official_documents.publication_date
  - BDNS fechaPublicacion

diagnostic_only:
  - failed ingestion_runs.finished_at
  - report generated_at
  - systemd timer last trigger without source-specific success
```

Only `observed` timestamps should become `FreshnessObservation.last_seen`.

## Source Mapping

| Source | Primary future input | Fallback future input | Current VPS input | Decision |
| --- | --- | --- | --- | --- |
| `BOE` | `data/rss_monitor/BOE/<date>/rss_discovery.jsonl` using latest record `discovered_at`. | Read-only SQLite `ingestion_runs` where `source_code='BOE'` and status is `success` or `no_publication`, using `finished_at`. | Missing. No monitor JSONL, no ingestion runs, no documents. | Needs monitor JSONL producer or SQLite observation adaptor plus actual BOE runs. |
| `BDNS` | Read-only SQLite `ingestion_runs` for BDNS latest/search/catalog runs with status `success`, using `finished_at`. | A dedicated BDNS runtime observation JSONL producer that performs a reviewed read-only latest-state check and writes only observation state. | Missing. No monitor JSONL, no ingestion runs, no documents. | Needs a producer/adaptor; current generic API monitor does not support BDNS. |
| `BOCM` | `data/rss_monitor/BOCM/<date>/rss_discovery.jsonl` using latest record `discovered_at`. | Read-only SQLite `ingestion_runs` where `source_code='BOCM'` and status is `success` or `no_publication`, using `finished_at`, if the paused adapter is explicitly re-enabled later. | Missing. No monitor JSONL, no ingestion runs, no documents. | Use RSS monitor JSONL first; do not rely on paused HTML/XML adapter paths. |

## Per-Source Rules

### BOE

Preferred signal:

```text
source: RSS monitor JSONL
path: data/rss_monitor/BOE/<target_date>/rss_discovery.jsonl
timestamp: max(discovered_at)
timestamp_type: observed
latest_record_date: max(published_at or updated_at), diagnostic only
```

Reasoning:

```text
BOE has a validated RSS feed and the existing freshness loader already understands monitor JSONL.
The BOE daily summary adapter also has useful ingestion_runs, including controlled no_publication,
but the current VPS has no BOE runs. SQLite should be a fallback, not the first mapping, because the
current freshness runtime is monitor-state oriented.
```

Missing behavior:

```text
If no BOE monitor JSONL and no acceptable BOE ingestion_run exists, BOE remains missing/NO-GO.
```

Calendar behavior:

```text
BOE Sundays may be controlled no_publication when proven by the BOE daily adapter.
Do not infer a calendar exception from the weekday alone in the freshness report.
```

### BDNS

Preferred signal:

```text
source: SQLite ingestion_runs, read-only
query scope: source_code='BDNS'
accepted status: success
timestamp: max(finished_at)
timestamp_type: observed
latest_record_date: BDNS fechaPublicacion or official_documents.publication_date, diagnostic only
```

Reasoning:

```text
BDNS is not currently supported by the generic api_monitor implementation. It has BDNS-specific
latest/search/detail/catalog adapters that create ingestion_runs when an operator runs them, but
Hermes must not execute those writers. If no independent BDNS run exists, freshness must remain
missing rather than pretending the API is fresh.
```

Missing behavior:

```text
If no successful BDNS observation exists, BDNS remains missing/NO-GO.
```

Producer gap:

```text
BDNS needs one of:
- a read-only SQLite freshness adaptor that consumes existing BDNS ingestion_runs when they exist;
- a separate operator-owned BDNS observation producer that writes a small JSONL observation file;
- a scoped BDNS API monitor implementation, reviewed separately, if the project wants JSONL parity.
```

### BOCM

Preferred signal:

```text
source: RSS monitor JSONL
path: data/rss_monitor/BOCM/<target_date>/rss_discovery.jsonl
timestamp: max(discovered_at)
timestamp_type: observed
latest_record_date: max(published_at or updated_at), diagnostic only
```

Reasoning:

```text
BOCM has validated RSS monitor support. The older HTML/XML metadata adapter path is documented as
paused in the registry because of endpoint instability. Freshness should therefore use RSS JSONL
first and should not treat the paused adapter as the normal critical signal.
```

Missing behavior:

```text
If no BOCM RSS monitor JSONL exists, BOCM remains missing/NO-GO unless a later task explicitly
re-enables and validates the BOCM adapter as an observation fallback.
```

## Required FreshnessObservation Shape

The next implementation should keep the current model and populate it with explicit provenance:

```json
{
  "source_code": "BOE",
  "last_seen": "2026-06-13T17:47:31Z",
  "threshold_hours": 72,
  "critical": true,
  "calendar_exception": null,
  "impact": "Observed via data/rss_monitor/BOE/2026-06-13/rss_discovery.jsonl",
  "provenance": {
    "input_type": "monitor_jsonl",
    "timestamp_type": "observed",
    "path": "data/rss_monitor/BOE/2026-06-13/rss_discovery.jsonl",
    "record_timestamp_field": "discovered_at",
    "latest_record_date": "2026-06-13"
  }
}
```

If the implementation keeps `SourceFreshness` unchanged, the provenance can be rendered inside
`impact` until a separate schema change is justified.

## Priority Order For The Next Implementation

```text
1. Extend the runtime reader to produce BOE and BOCM observations from existing RSS monitor JSONL.
   This is already mostly supported by the current loader; the missing part is producing real JSONL.

2. Add a read-only SQLite observation adaptor for existing ingestion_runs:
   - BOE success/no_publication
   - BDNS success
   - BOCM success/no_publication only if explicitly accepted as fallback

3. Decide whether BDNS needs a dedicated observation producer because current VPS state has no
   BDNS ingestion_runs and generic api_monitor does not support BDNS.
```

## Forbidden For This Mapping

This task does not:

```text
- activate a scheduler
- add or modify systemd units/timers
- write SQLite
- execute ingest-monitor-date
- run BOE/BDNS/BOCM live fetches
- mutate config/sources.yaml
- create official_documents
- create evidence records
- create candidates
- publish
- run downstream smokes
- open automatic issues
```

## Merge Criteria For Follow-Up Implementation

Do not activate a timer until a later PR proves at least one of these:

```text
- BOE and BOCM monitor JSONL exist and the freshness report reads them as observed timestamps.
- BDNS has a documented read-only observation source with a real successful timestamp.
- Missing critical sources still fail closed, but the missing state is a deliberate daily signal.
```

Until then, the daily report would be technically correct but low-signal:

```text
VERDICT: NO-GO because BOE, BDNS, and BOCM observations are missing.
```

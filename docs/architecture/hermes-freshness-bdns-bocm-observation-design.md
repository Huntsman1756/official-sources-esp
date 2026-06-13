# Hermes Freshness BDNS/BOCM Observation Design

Status: design-only

Task:

```text
TASK-HERMES-FRESHNESS-BDNS-BOCM-OBSERVATION-DESIGN-001
```

## Purpose

Define a safe observation path for stale critical sources before activating any freshness schedule.

Current state:

```text
Hermes freshness engine: works
freshness-observations producer: works
freshness-report --observations-jsonl: works
BOE: healthy from existing BOE daily runtime state
BDNS: stale
BOCM: stale
scheduler: blocked
```

The missing piece is not report logic. The missing piece is a legitimate runtime path that produces
fresh operational observations for `BDNS` and `BOCM`.

## Non-Goals

This design does not:

```text
- activate freshness scheduler
- create or modify systemd units/timers
- run live fetches
- run ingest-monitor-date
- write SQLite
- mutate config/sources.yaml
- create official_documents/evidence/candidates/publication
- run downstream smokes
- open automatic issues
```

Hermes remains a report/audit consumer. It must not become the actor that fixes stale sources.

## Evidence Base

The stale-source investigation found:

```text
BOE latest success: 2026-06-13T07:41:10.656169+00:00
BDNS latest success: 2026-05-31T13:47:15.960144+00:00
BOCM latest accepted observation: 2026-05-21T20:19:13.900362+00:00
```

Systemd evidence:

```text
official-sources-boe-daily.timer: enabled
official-sources-integrity-check.timer: enabled
official-sources-hermes-auditor.timer: enabled
BDNS refresh unit: absent
BOCM refresh unit: absent
```

Runtime evidence:

```text
/opt/official-sources/app/data: no current monitor/freshness JSONL
/opt/official-sources/data/exports: older BDNS exports only
/var/lib/hermes-official-sources-auditor/freshness-reports: report output only
```

## Timestamp Contract

Freshness must continue to use operational observation timestamps only.

Accepted `observed_at` sources:

```text
- monitor JSONL discovered_at / observed_at
- successful existing ingestion_runs.finished_at
- controlled no_publication ingestion_runs.finished_at where the source command proves the source was checked
- future source-observation JSONL completion timestamp after a bounded successful official-source check
```

Not accepted as `observed_at`:

```text
- BDNS fechaPublicacion
- RSS published_at / updated_at
- official_documents.publication_date
- failed ingestion_runs.finished_at
- systemd timer trigger time without source-specific success
- freshness report generated_at
```

Publication or record dates may appear as `latest_record_date` diagnostics only.

## State Layout

Future runtime observation state should live outside the audited checkout:

```text
state-root: /var/lib/hermes-official-sources-auditor
monitor runtime root: /var/lib/hermes-official-sources-auditor/freshness-runtime
monitor JSONL: /var/lib/hermes-official-sources-auditor/freshness-runtime/data/<monitor_kind>_monitor/<SOURCE>/<DATE>/*_discovery.jsonl
observation JSONL: /var/lib/hermes-official-sources-auditor/freshness-observations/latest.jsonl
reports: /var/lib/hermes-official-sources-auditor/freshness-reports/
```

Rationale:

```text
- do not write generated runtime monitor files into /opt/official-sources/app
- keep Hermes report state and observation state in the existing Hermes state root
- keep the producer compatible with --runtime-root by making freshness-runtime contain data/...
```

Example producer consumption:

```bash
official-sources hermes freshness-observations \
  --runtime-root /var/lib/hermes-official-sources-auditor/freshness-runtime \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --source BOE \
  --source BDNS \
  --source BOCM \
  --output /var/lib/hermes-official-sources-auditor/freshness-observations/latest.jsonl
```

The SQLite DB is read-only input to the producer. It is not a write target.

## BOCM Design

Preferred observation path:

```text
existing command: official-sources rss monitor
source: BOCM
mode: explicit --write
write target: freshness-runtime/data/rss_monitor
timestamp: discovered_at from rss_discovery.jsonl
```

Proposed command shape:

```bash
official-sources rss monitor \
  --source BOCM \
  --date today \
  --limit 1 \
  --write \
  --output-root /var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor
```

Expected JSONL path:

```text
/var/lib/hermes-official-sources-auditor/freshness-runtime/data/rss_monitor/BOCM/<YYYY-MM-DD>/rss_discovery.jsonl
```

Status mapping:

```text
success:
  RSS request succeeds, parser emits at least one metadata record, and JSONL is written.

missing/stale:
  No current RSS JSONL exists or no usable discovered_at/observed_at is present.

failed:
  RSS command exits non-zero or writes invalid JSONL.
```

`no_publication` should not be inferred from a zero-record RSS run unless a later source-specific
monitor explicitly emits controlled no-publication metadata. Until then, zero usable records should
remain missing/stale rather than pretending a successful observation exists.

The paused BOCM HTML/XML metadata adapter is not the preferred freshness path. It may remain a
diagnostic fallback only after a separate task explicitly revalidates it.

## BDNS Design

BDNS currently has useful source-specific commands, but they are not equivalent to a monitor-only
freshness observer.

Existing commands:

```text
ingest-bdns-latest       writes SQLite official source state
ingest-bdns-call         writes SQLite official source state
ingest-bdns-catalog      writes SQLite reusable local evidence/cache state
ingest-bdns-concesiones  writes SQLite scoped concessions state
search-bdns-calls        bounded live search preview, no observation JSONL writer
preview-bdns-catalog     preview only
preview-bdns-concesiones preview only
```

Design decision:

```text
Hermes must not schedule BDNS ingestion commands.
Hermes may consume successful BDNS ingestion_runs when an operator-owned process creates them.
Freshness automation should not use ingest-bdns-* as a hidden freshness fix.
```

Recommended implementation path:

```text
1. Keep current read-only SQLite ingestion_runs adaptor as a fallback.
2. Add a separate BDNS observation producer command in a future PR if daily BDNS freshness is needed.
3. The BDNS observation producer should perform a bounded official API check and write observation
   JSONL only; it must not write SQLite, official_documents, evidence, candidates, publication, or
   downstream outputs.
```

Future BDNS observation command shape, to be implemented separately:

```bash
official-sources bdns observe-latest \
  --limit 1 \
  --output /var/lib/hermes-official-sources-auditor/freshness-runtime/data/api_monitor/BDNS/<YYYY-MM-DD>/api_discovery.jsonl
```

This command does not exist yet. It is intentionally named as an observation command, not ingestion.

Accepted BDNS `observed_at`:

```text
- command completion timestamp after HTTP 200 and valid parse of a bounded latest/search response
- existing successful BDNS ingestion_runs.finished_at when produced by explicit operator action
```

Rejected BDNS `observed_at`:

```text
- fechaPublicacion
- official_documents.publication_date
- old BDNS export file mtime
- concessions preview timestamp unless the command is explicitly scoped as freshness observation
```

Status mapping:

```text
success:
  BDNS official API responds, bounded payload parses, and observation JSONL is written.

stale:
  Latest accepted BDNS observed_at is older than the SLO.

missing:
  No accepted BDNS observation exists.

failed:
  API command fails, parse fails, JSONL is invalid, or no output file is produced.
```

## Scheduling Policy

Do not attach this to the existing integrity check.

Rationale:

```text
- integrity-check currently validates local artifact/source state; it is not a source refresh runner
- mixing source observation fetches into integrity-check would blur validation and observation
- failures should be attributable per source before they feed Hermes freshness reports
```

Preferred future order:

```text
1. source-observation runner writes source observation inputs
2. freshness-observations compacts monitor/DB state into latest.jsonl
3. scheduled-freshness-report reads latest.jsonl and writes markdown
4. Hermes strict audit remains separate
```

Future service naming, if approved later:

```text
official-sources-critical-observations.service
official-sources-critical-observations.timer
official-sources-hermes-freshness-report.service
official-sources-hermes-freshness-report.timer
```

No timer should be activated until manual local and VPS smokes prove:

```text
- BOCM RSS JSONL is produced in freshness-runtime
- BDNS has either a current operator-owned ingestion_run or a new observation-only JSONL producer
- freshness-observations writes latest.jsonl
- freshness-report --observations-jsonl reports BOE/BDNS/BOCM from real observations
- NO-GO remains report content, not an auto-fix trigger
```

## Failure Semantics

Observation runner failures must be visible and source-specific.

Required report fields for a future runner:

```text
source
command
exit_code
status
observed_at
output_path
records_seen
error_message
sqlite_written=false
registry_mutated=false
downstream_writes=false
```

Rules:

```text
- failed BOCM RSS run must not delete the previous observation
- failed BDNS observation must not create a fake observed_at
- stale previous observations remain stale and visible
- successful source observations may update latest.jsonl only after input JSONL validates
```

## Implementation Acceptance Criteria

For a future implementation PR:

```text
GO if:
- BOCM uses existing rss monitor JSONL or an equally monitor-only source-specific path
- BDNS either remains explicit operator-owned DB state or gets a new observation-only command
- writes are limited to freshness-runtime JSONL and freshness-observations JSONL
- observed_at is operational, not published_at/fechaPublicacion
- tests cover success, stale, missing, failed, and invalid JSONL
- local smoke and VPS smoke are documented before scheduler activation

NO-GO if:
- Hermes executes ingest-bdns-* or ingest-bocm-date as an auto-fix
- BDNS publication dates become freshness timestamps
- BOCM falls back to the paused HTML/XML adapter without a revalidation task
- generated monitor state is written into the audited checkout by default
- scheduler is activated in the same PR as the observation-path implementation
```

## Current Operational Verdict

```text
PR type: design-only
implementation: not started
scheduler: NO-GO
BDNS next step: decide/add observation-only producer or accept operator-owned DB refresh cadence
BOCM next step: implement/smoke RSS monitor JSONL into freshness-runtime
Hermes role: consume/report/audit only
```

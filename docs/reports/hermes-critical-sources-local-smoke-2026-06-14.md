# Hermes Critical Sources Local Smoke - 2026-06-14

Task:

```text
TASK-HERMES-FRESHNESS-CRITICAL-SOURCES-LOCAL-SMOKE-001
```

## Purpose

Run a local post-#54 critical freshness smoke for:

```text
BOE
BDNS
BOCM
```

The smoke uses a temporary local state root and does not activate any scheduler.

## Scope

Allowed:

```text
- local temp-state writes under %TEMP%
- explicit BOE RSS monitor write into temp freshness-runtime
- explicit BOCM RSS observation wrapper into temp freshness-runtime
- explicit BDNS observation wrapper into temp freshness-runtime
- freshness-observations compaction into temp latest-critical.jsonl
- freshness-report over latest-critical.jsonl
```

Forbidden and not performed:

```text
- scheduler activation
- systemd/timer changes
- VPS mutation
- SQLite writes
- ingest-bdns-*
- ingest-monitor-date
- registry mutation
- official_documents/evidence/candidates/publication
- product/external project writes
- automatic issues
```

## Local State

```text
state_root=C:\Users\rome_\AppData\Local\Temp\hermes-critical-sources-smoke-20260614-061307
runtime_root=C:\Users\rome_\AppData\Local\Temp\hermes-critical-sources-smoke-20260614-061307\freshness-runtime
observations=C:\Users\rome_\AppData\Local\Temp\hermes-critical-sources-smoke-20260614-061307\freshness-observations\latest-critical.jsonl
report=C:\Users\rome_\AppData\Local\Temp\hermes-critical-sources-smoke-20260614-061307\freshness-reports\critical-smoke-rfc2822-fixed.md
```

## Commands

BOE RSS monitor:

```powershell
python -m official_sources.cli rss monitor `
  --source BOE `
  --date 2026-06-14 `
  --limit 1 `
  --write `
  --output-root <state_root>\freshness-runtime\data\rss_monitor
```

BOCM observation:

```powershell
python -m official_sources.cli hermes bocm-rss-observation `
  --repo-root . `
  --state-root <state_root> `
  --official-sources-bin .\.venv\Scripts\official-sources.exe `
  --date today `
  --limit 1
```

BDNS observation:

```powershell
python -m official_sources.cli hermes bdns-observation `
  --repo-root . `
  --state-root <state_root> `
  --official-sources-bin .\.venv\Scripts\official-sources.exe `
  --limit 1
```

Observation compaction:

```powershell
python -m official_sources.cli hermes freshness-observations `
  --runtime-root <state_root>\freshness-runtime `
  --source BOE `
  --source BDNS `
  --source BOCM `
  --output <state_root>\freshness-observations\latest-critical.jsonl
```

Freshness report:

```powershell
python -m official_sources.cli hermes freshness-report `
  --observations-jsonl <state_root>\freshness-observations\latest-critical.jsonl `
  --now 2026-06-14T12:00:00Z `
  --critical-source BOE `
  --critical-source BDNS `
  --critical-source BOCM `
  --expected-source BOE `
  --expected-source BDNS `
  --expected-source BOCM `
  --output <state_root>\freshness-reports\critical-smoke-rfc2822-fixed.md
```

## Important Findings

The first BOE attempt used:

```text
--date today
```

Result:

```text
BOE_RSS_EXIT=2
--date must use YYYY-MM-DD format
```

This is expected CLI behavior for `rss monitor`; the corrected command used:

```text
--date 2026-06-14
```

The second attempt found a real freshness-observation bug:

```text
invalid timestamp: Sat, 13 Jun 2026 00:00:00 +0200
```

Cause:

```text
BOE RSS records can emit diagnostic published_at values in RFC 2822 format.
freshness-observations treated diagnostic record dates as ISO-only.
```

Fix:

```text
freshness-observations now accepts RFC 2822 timestamps as record-date diagnostics.
observed_at still comes from discovered_at/observed_at only.
published_at remains diagnostic latest_record_date and does not feed freshness observed_at.
```

## Final Local Result

Observation compaction:

```text
observations_written=3
OBSERVATIONS_EXIT=0
```

Freshness report:

```text
VERDICT: GO
REPORT_EXIT=0
```

Sources:

```text
BDNS healthy
  last_seen=2026-06-14T04:13:09.821746Z
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

## Validation

```text
RED:
python -m pytest tests/test_hermes_freshness_observation_producer.py::test_collects_monitor_observation_accepts_rfc2822_record_date -q
-> failed with invalid timestamp: Sat, 13 Jun 2026 00:00:00 +0200

GREEN:
python -m pytest tests/test_hermes_freshness_observation_producer.py::test_collects_monitor_observation_accepts_rfc2822_record_date -q
-> 1 passed

python -m pytest tests/test_hermes_freshness_observation_producer.py tests/test_hermes_freshness_report.py tests/test_hermes_bdns_observation.py tests/test_hermes_bocm_rss_observation.py -q
-> 32 passed
```

## Operational Verdict

```text
local critical freshness smoke: GO
BOE: healthy
BDNS: healthy
BOCM: healthy
scheduler: still NO-GO
VPS smoke: not run in this PR
```

VPS smoke must be run only after this fix is merged and the VPS checkout is aligned to the merged
commit.

# Hermes Freshness Stale Sources Investigation - 2026-06-13

Status: completed

Task:

```text
TASK-HERMES-FRESHNESS-STALE-SOURCES-INVESTIGATION-001
```

## Purpose

Investigate why the VPS freshness report now returns real observations but still reports stale
critical sources:

```text
BOE  healthy
BDNS stale
BOCM stale
VERDICT: NO-GO
```

This was an investigation-only pass. It did not activate the freshness scheduler and did not run
any corrective ingestion.

## Scope

Allowed:

```text
- inspect systemd units and timers
- read service unit definitions
- read SQLite state in read-only mode
- inspect runtime monitor/output paths
- run Hermes strict audit after inspection
- document findings
```

Forbidden:

```text
- activate scheduler
- create or modify systemd units/timers
- restart services
- run live fetches
- run ingest-monitor-date
- write SQLite
- mutate registry
- create official_documents/evidence/candidates/publication
- run downstream smokes
- open automatic issues
```

## VPS Context

VPS:

```text
host: 157.90.22.40
alias: mcpspain-official-sources-vps
checkout: /opt/official-sources/app
service DB: /opt/official-sources/data/official_sources.sqlite
```

At inspection time the VPS checkout remained on the last code-bearing freshness merge:

```text
HEAD: 6b689a7
git status: ## main...origin/main
```

Remote `main` had advanced to docs-only PR #49:

```text
remote_head_observed_sha: ea5db0bc0f4a5d42cd9f7b86d1208ebeb09554c3
```

The VPS was not fast-forwarded in this task because the investigation scope was read-only.

## Systemd Evidence

Installed official-sources timers:

```text
official-sources-hermes-auditor.timer
official-sources-boe-daily.timer
official-sources-integrity-check.timer
official-sources-hermes-scheduled-validation.timer
```

Unit files:

```text
official-sources-boe-daily.service                   static
official-sources-hermes-auditor.service              static
official-sources-hermes-scheduled-validation.service static
official-sources-integrity-check.service             static
official-sources-boe-daily.timer                     enabled
official-sources-hermes-auditor.timer                enabled
official-sources-hermes-scheduled-validation.timer   enabled
official-sources-integrity-check.timer               enabled
```

There are no installed or enabled BDNS or BOCM refresh units.

The BOE daily service runs BOE-specific ingestion and artifact download:

```text
ExecStart=/opt/official-sources/app/.venv/bin/official-sources ingest-boe-summary --date today
ExecStart=/opt/official-sources/app/.venv/bin/official-sources download-boe-artifacts --date today --types xml,html
ExecStart=/opt/official-sources/app/.venv/bin/official-sources status --date today
```

The integrity service checks current BOE state; it does not refresh BDNS or BOCM:

```text
ExecStart=/opt/official-sources/app/.venv/bin/official-sources integrity-check --date today
ExecStart=/opt/official-sources/app/.venv/bin/official-sources status --date today
```

System health after inspection:

```text
systemctl --failed: 0 loaded units listed
```

## Runtime Output Evidence

Runtime path inspection found no active monitor JSONL producer output for the critical sources under
the app checkout:

```text
/opt/official-sources/app/data: no monitor/freshness/jsonl paths found
```

The service data directory contains older BDNS exports, but not current monitor observation JSONL:

```text
/opt/official-sources/data/exports/bdns_grants_enriched.jsonl
/opt/official-sources/data/exports/bdns_concessions_877699_sanitized.jsonl
/opt/official-sources/data/exports/bdns_business_grants.jsonl
```

Hermes report state exists in its own state root:

```text
/var/lib/hermes-official-sources-auditor/freshness-reports/
```

## SQLite Evidence

The read-only database inspection used:

```text
file:/opt/official-sources/data/official_sources.sqlite?mode=ro
```

Distinct source codes are exact, so this is not an alias mismatch:

```text
BDNS
BOCM
BOE
```

Latest grouped ingestion runs:

```text
BDNS success        runs=19  latest_finished_at=2026-05-31T13:47:15.960144+00:00
BOCM success        runs=13  latest_finished_at=2026-05-21T20:19:13.900362+00:00
BOCM no_publication runs=2   latest_finished_at=2026-05-21T20:18:55.503394+00:00
BOCM failed         runs=5   latest_finished_at=2026-05-21T20:49:16.593666+00:00
BOE success         runs=201 latest_finished_at=2026-06-13T07:41:10.656169+00:00
```

Most recent BDNS runs are all from 2026-05-31:

```text
id=417 source=BDNS target=concesiones:877699 status=success finished_at=2026-05-31T13:47:15.960144+00:00
id=416 source=BDNS target=latest             status=success finished_at=2026-05-31T12:44:40.307522+00:00
id=415 source=BDNS target=latest             status=success finished_at=2026-05-31T12:43:58.481411+00:00
```

Most recent BOCM successful/no-publication observations are from 2026-05-21:

```text
id=248 source=BOCM target=2026-05-05 status=success        finished_at=2026-05-21T20:19:13.900362+00:00
id=247 source=BOCM target=2026-05-04 status=success        finished_at=2026-05-21T20:19:05.642918+00:00
id=246 source=BOCM target=2026-05-03 status=no_publication finished_at=2026-05-21T20:18:55.503394+00:00
```

The latest BOCM attempts after that were failures against 2026-05-06:

```text
id=251 source=BOCM target=2026-05-06 status=failed finished_at=2026-05-21T20:49:16.593666+00:00
error=BOCM search_day request for 2026-05-06 timed out after 4 attempts: timed out
```

Stored document summaries are consistent with stale observations:

```text
BDNS documents=25  latest_publication_date=2026-05-29 latest_updated_at=2026-05-31T12:44:40.292350+00:00
BOCM documents=982 latest_publication_date=2026-05-05 latest_updated_at=2026-05-21T20:19:13.886324+00:00
```

Publication dates remain diagnostic only. Freshness is still based on operational observation
timestamps, not on `publication_date`.

## Diagnosis

The stale result is real and expected from the current runtime shape.

```text
BOE is fresh because the VPS has an active BOE daily timer and recent successful BOE ingestion_runs.
BDNS is stale because the latest successful BDNS run is historical/manual state from 2026-05-31.
BOCM is stale because the latest accepted BOCM observation is historical state from 2026-05-21, and
the later BOCM attempts failed on endpoint timeout.
```

There is no evidence of a currently installed source refresh path for BDNS or BOCM:

```text
no BDNS systemd timer/service
no BOCM systemd timer/service
no current BDNS/BOCM monitor JSONL output
no scheduled RSS monitor writer for BOCM
no scheduled read-only BDNS observation producer
```

This is not a freshness-report bug. The report is now surfacing an operational coverage gap:

```text
critical source observations exist
BOE observation is recent
BDNS and BOCM observations are old
scheduler activation remains NO-GO
```

## Post-Inspection Hermes Audit

Strict audit after inspection produced no failed gates, but did warn that remote `main` had advanced
to the docs-only PR #49 SHA while the VPS release contract still points at `6b689a7`:

```text
VERDICT: WARNING
expected_head_sha: 6b689a72b0b313192639af32a1facec538ada495
actual_head_sha: 6b689a72b0b313192639af32a1facec538ada495
remote_head_observed_sha: ea5db0bc0f4a5d42cd9f7b86d1208ebeb09554c3
git_worktree_clean: True
failed gates: none
warning: git ls-remote observed remote head differs from expected release SHA
```

This warning is release-contract drift after a docs-only merge, not a BDNS/BOCM freshness failure.
No VPS alignment was performed in this investigation.

## Recommended Next Step

Do not activate the freshness scheduler yet.

Open a separate implementation/design task:

```text
TASK-HERMES-FRESHNESS-BDNS-BOCM-OBSERVATION-PATH-001
```

Recommended contract:

```text
Allowed:
- define a source-specific freshness observation path for BDNS and BOCM
- prefer BOCM RSS monitor JSONL over the paused HTML/XML adapter
- decide whether BDNS needs a read-only observation producer or an explicit operator refresh cadence
- write only observation JSONL if implementation is approved
- test with fixtures and a VPS smoke

Forbidden:
- activate scheduler before BDNS/BOCM have useful observations
- run live corrective fetches inside Hermes
- run ingest-monitor-date
- write SQLite from Hermes
- mutate registry
- create official_documents/evidence/candidates/publication
- downstream writes
- automatic fixes
```

## Conclusion

```text
investigation: GO
BDNS stale cause: no current scheduled/automatic observation producer; latest success is 2026-05-31
BOCM stale cause: no current scheduled RSS observation producer; adapter history stopped on 2026-05-21 with later timeouts
BOE fresh cause: active daily BOE timer
freshness scheduler: still NO-GO
```

Hermes is doing the right thing: it is not inventing freshness. It is reporting that two critical
sources no longer have recent operational observations.

# BOCYL 30-Day Metadata Backfill - 2026-05-21

## Scope

This report records a controlled BOCYL metadata-only backfill on the project VPS.

Rules applied:

- no PDF/XML/HTML artifact downloads;
- no source candidates;
- no candidate extraction;
- no EduAyudas work;
- no `la-ayuda` work;
- no downstream writes;
- no MCP exposure;
- no broader backfill;
- no other adapters implemented.

## Deployment

VPS:

```text
host=157.90.22.40
ssh_target=mcpspain-official-sources-vps
user=root
hostname=ubuntu-4gb-nbg1-8
```

Deployed repository:

```text
path=/opt/official-sources/app
branch=main
deployed_commit=a46c34c
```

The VPS was updated from `3e68dea` to `a46c34c` with:

```bash
cd /opt/official-sources/app
git fetch origin
git pull --ff-only origin main
```

The installed virtualenv CLI recognized `ingest-bocyl-date`.

## Date Range

```text
source_code=BOCYL
range=2026-04-21 -> 2026-05-20
dates_processed=30
```

Command pattern:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bocyl-date --date "$d"
```

The backfill ran one date at a time with a one-second pause between dates.

Log:

```text
/opt/official-sources/logs/bocyl_30d_backfill_20260523_0926.log
```

## Results

Summary:

| metric | value |
| --- | ---: |
| dates processed | 30 |
| success dates | 20 |
| no-publication dates | 10 |
| failed dates | 0 |
| documents fetched | 773 |
| documents new | 773 |
| documents updated | 0 |
| HTTP status summary | `200:30` |

Successful dates and issue identifiers:

| date | issue_identifier | documents |
| --- | --- | ---: |
| 2026-04-21 | 75/2026 | 34 |
| 2026-04-22 | 76/2026 | 38 |
| 2026-04-24 | 77/2026 | 24 |
| 2026-04-27 | 78/2026 | 47 |
| 2026-04-28 | 79/2026 | 28 |
| 2026-04-29 | 80/2026 | 28 |
| 2026-04-30 | 81/2026 | 56 |
| 2026-05-04 | 82/2026 | 39 |
| 2026-05-05 | 83/2026 | 41 |
| 2026-05-06 | 84/2026 | 45 |
| 2026-05-07 | 85/2026 | 44 |
| 2026-05-08 | 86/2026 | 44 |
| 2026-05-11 | 87/2026 | 39 |
| 2026-05-12 | 88/2026 | 33 |
| 2026-05-13 | 89/2026 | 29 |
| 2026-05-14 | 90/2026 | 39 |
| 2026-05-15 | 91/2026 | 39 |
| 2026-05-18 | 92/2026 | 44 |
| 2026-05-19 | 93/2026 | 40 |
| 2026-05-20 | 94/2026 | 42 |

No-publication dates:

```text
2026-04-23
2026-04-25
2026-04-26
2026-05-01
2026-05-02
2026-05-03
2026-05-09
2026-05-10
2026-05-16
2026-05-17
```

## Pagination / Page-Size Risk

The current BOCYL MVP uses `limit=100`.

Observed maximum:

```text
max_docs_in_single_day=2026-04-30:56
page_size_limit_hits=none
```

No date reached or exceeded the current page size. The next hardening task should
still add an explicit completeness guard using the API `total_count` so future
dates cannot silently truncate if `total_count > limit`.

## Pre/Post Counts

Before run:

```text
BOCYL official_documents=0
BOCYL ingestion_runs=0
artifact_download_attempts=442
source_candidates=125
artifact_size=30M
```

After run:

```text
BOCYL official_documents=773
BOCYL ingestion_runs=30
artifact_download_attempts=442
source_candidates=125
artifact_size=30M
BOCYL pdf document_files=0
BOCYL xml document_files=0
BOCYL raw_api_response document_files=773
```

Artifact attempts and source candidates were unchanged.

## Database Validation

Before:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

After:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## Backups

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_bocyl_30d_backfill_20260523_092612.sqlite
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_bocyl_30d_backfill_20260523_092845.sqlite
```

Both were created through the project CLI `db backup` command.

## MCP Privacy Check

Command:

```bash
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener observed
```

## Known Limitations

- BOCYL MVP does not yet implement pagination beyond `limit=100`.
- HTML date-page cross-check is not run during backfill.
- XML/PDF/HTML URLs are preserved as metadata only; artifact downloads remain out of scope.
- Candidate dry-run has not been run for BOCYL.

## Next Recommended Task

```text
TASK-AUTO-BOCYL-004 - BOCYL candidate dry-run
```

Guardrails:

- dry-run only;
- no source candidate writes;
- no PDF/XML/HTML artifact downloads;
- no downstream writes;
- include pagination/completeness guard hardening before any broader backfill.

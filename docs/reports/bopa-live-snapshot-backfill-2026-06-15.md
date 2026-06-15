# BOPA Live Snapshot Backfill

Task: `TASK-OFFICIAL-SOURCES-BOPA-LIVE-SNAPSHOT-BACKFILL-001`

Date: 2026-06-15

## Scope

Backfill BOPA `document_files` integrity rows on the live official-sources SQLite for the existing
BOPA monitor slice.

Allowed write surface:

- live official-sources SQLite only;
- `ingestion_runs`;
- `official_documents` updates from the same BOPA monitor materialization path;
- `document_files`;
- `integrity_checks`.

Forbidden and preserved:

- no source candidates;
- no evidence-grade records;
- no artifact/PDF downloads;
- no downstream writes;
- no EduBecas DB writes;
- no publication/drafts;
- no runtime checkout merge/pull/deploy;
- no systemd/timer/cap/Hermes changes.

## Runtime Boundary

The live checkout was not fast-forwarded:

```text
runtime_head=1d5a20b
main...origin/main [behind 1]
origin/main=d0448f3
external_contract_expected=1d5a20baae785f13c4800529d954d6e07f324e16
```

To avoid mixing release-contract/runtime movement with this DB backfill, the run used a temporary
checkout of `d0448f3`:

```text
temp_checkout=/var/tmp/official-sources-bopa-artifact-d0448f3e9a94c781ae9d9115a83257d20adf1270
temp_head=d0448f3
```

The existing venv under `/opt/official-sources/app/.venv` executed the temporary checkout code via
`PYTHONPATH`.

## Preflight

```text
quick_check=ok
source=BOPA
source_id=799
documents=50
dates=2026-06-05:50
files=0
raw_files=0
integrity_checks=0
source_candidates=0
artifact_download_attempts=0
```

Verified backup:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_bopa_artifact_integrity_20260615_055050.sqlite
source_quick_check=ok
backup_quick_check=ok
backup_size_bytes=120369152
```

## Run

```text
command_started=ingest-monitor-date source_code=BOPA target_date=2026-06-05 monitor=html db_path=/opt/official-sources/data/official_sources.sqlite writes=sqlite_materialization
status=success
ingestion_run_id=520
source_created=false
documents_fetched=50
documents_new=0
documents_updated=50
documents_upserted=50
partial_materialization=false
failure_record_index=none
candidate_creation_allowed=false
evidence_created=false
artifact_downloads=false
product_writes=false
registry_config_mutated=false
```

## Postflight

```text
quick_check_after=ok
source_id=799
documents=50
dates=2026-06-05:50
files=50
raw_files=50
html_media_files=50
same_hash_files=50
integrity_checks=50
source_candidates=0
artifact_download_attempts=0
latest_ingestion_run=520|BOPA|success|50|0|50
runtime_head_after=1d5a20b
runtime_branch_after=main...origin/main [behind 1]
```

## Result

BOPA live rows now have integrity-backed monitor snapshot artifacts without creating candidates,
evidence-grade rows, artifact downloads, downstream writes, runtime changes, or public outputs.

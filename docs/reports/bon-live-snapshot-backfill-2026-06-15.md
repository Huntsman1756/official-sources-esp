# BON Live Snapshot Backfill

Task: `TASK-OFFICIAL-SOURCES-BON-LIVE-SNAPSHOT-BACKFILL-001`

Date: 2026-06-15

## Scope

Backfill BON `document_files` integrity rows on the live official-sources SQLite for the existing
BON monitor slice.

Allowed write surface:

- live official-sources SQLite only;
- `ingestion_runs`;
- `official_documents` updates from the same BON monitor materialization path;
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
```

To avoid mixing release-contract/runtime movement with this DB backfill, the run used a temporary
checkout of `e2e2688`:

```text
temp_checkout=/var/tmp/official-sources-bon-artifact-e2e2688f42bdbd016ef03f1d219d5d91059f0760
temp_head=e2e2688
```

The existing venv under `/opt/official-sources/app/.venv` executed the temporary checkout code via
`PYTHONPATH`.

## Preflight

```text
quick_check_before=ok
source=BON
source_id=803
documents=46
dates=2026-06-05:46
files_before=0
raw_files_before=0
integrity_checks_before=0
source_candidates_before=0
artifact_download_attempts_before=0
```

Verified backup:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_bon_artifact_integrity_20260615_060747.sqlite
source_quick_check=ok
backup_quick_check=ok
backup_size_bytes=120446976
```

## Run

```text
command_started=ingest-monitor-date source_code=BON target_date=2026-06-05 monitor=html db_path=/opt/official-sources/data/official_sources.sqlite writes=sqlite_materialization
status=success
ingestion_run_id=521
source_created=false
documents_fetched=46
documents_new=0
documents_updated=46
documents_upserted=46
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
source_id=803
documents=46
dates=2026-06-05:46
files=46
raw_files=46
html_media_files=46
same_hash_files=46
integrity_checks=46
source_candidates=0
artifact_download_attempts=0
latest_ingestion_run=521|BON|success|46|0|46
runtime_head_after=1d5a20b
runtime_branch_after=main...origin/main [behind 1]
```

## Result

BON live rows now have integrity-backed monitor snapshot artifacts without creating candidates,
evidence-grade rows, artifact downloads, downstream writes, runtime changes, or public outputs.

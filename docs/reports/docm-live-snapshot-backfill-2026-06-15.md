# DOCM Live Snapshot Backfill

Task: `TASK-OFFICIAL-SOURCES-DOCM-LIVE-SNAPSHOT-BACKFILL-001`

Date: 2026-06-15

## Scope

Backfill DOCM `document_files` integrity rows on the live official-sources SQLite for the existing
DOCM monitor slice.

Allowed write surface:

- live official-sources SQLite only;
- `ingestion_runs`;
- `official_documents` updates from the same DOCM monitor materialization path;
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

The live checkout was not fast-forwarded because it was divergent:

```text
runtime_head=bdddd07
main...origin/main [ahead 2, behind 6]
origin/main=3fb4ad6
```

To avoid mixing release-contract drift with this DB backfill, the run used a temporary checkout of
`3fb4ad6`:

```text
temp_checkout=/var/tmp/official-sources-docm-artifact-3fb4ad6f0a90d528355af87e5c4d7a1a521a7a03
temp_head=3fb4ad6
```

The existing venv under `/opt/official-sources/app/.venv` executed the temporary checkout code via
`PYTHONPATH`.

## Preflight

```text
db_validate_before:
database_path=/opt/official-sources/data/official_sources.sqlite current_version=10 latest_version=10 status=valid

DOCM before:
documents=32
files=0
raw_files=0
source_candidates=0
artifact_download_attempts=0
```

Verified backup:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_docm_artifact_integrity_20260615_043712.sqlite
pages=29379
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=120336384
status=success
```

## Run

```text
command_started=ingest-monitor-date source_code=DOCM target_date=2026-06-05 monitor=html db_path=/opt/official-sources/data/official_sources.sqlite writes=sqlite_materialization
status=success
ingestion_run_id=519
source_created=false
documents_fetched=32
documents_new=0
documents_updated=32
documents_upserted=32
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
db_validate_after:
database_path=/opt/official-sources/data/official_sources.sqlite current_version=10 latest_version=10 status=valid

DOCM after:
documents=32
files=32
raw_files=32
html_media_files=32
same_hash_files=32
integrity_checks=32
source_candidates=0
artifact_download_attempts=0
```

Focused final validation:

```text
matching_files=32
source_candidates=0
artifact_download_attempts=0
db_validate=status=valid
```

## Separate Drift

`official-sources-hermes-auditor.service` was already failed during preflight. It is unrelated to
the DOCM SQLite backfill.

Strict report:

```text
VERDICT: NO-GO
expected_head_sha=1045bf794b8622d2f02213e70ec566628388a05d
actual_head_sha=bdddd07885bd203caab880cbbebd44db6e217102
remote_head_observed_sha=3fb4ad6f0a90d528355af87e5c4d7a1a521a7a03
failed_gate=observed checkout HEAD differs from expected release SHA
```

This needs a separate release-contract/runtime reconciliation task. It was not fixed here.

## Result

DOCM live rows now have integrity-backed monitor snapshot artifacts without creating candidates,
evidence-grade rows, artifact downloads, downstream writes, runtime changes, or public outputs.

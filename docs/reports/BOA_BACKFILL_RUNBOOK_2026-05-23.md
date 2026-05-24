# BOA 30-Day Metadata Backfill Runbook - 2026-05-23

## Scope

Task: `TASK-AUTO-BOA-003-RUNBOOK`.

This runbook prepares the exact VPS procedure for a controlled BOA 30-day metadata-only
backfill. It does not execute the backfill.

Target range:

```text
source_code=BOA
date_from=2026-04-21
date_to=2026-05-20
dates_expected=30
```

Allowed operation:

```text
official-sources ingest-boa-date --date YYYY-MM-DD
```

Explicitly out of scope:

- no artifact downloads;
- no PDF/XML/HTML download commands;
- no source-candidate commands;
- no candidate creation;
- no downstream preview/import/write;
- no `la-ayuda`, `eduayudas`, or other downstream project work;
- no broader source backfill;
- no ingestion beyond the exact BOA date range above.

## Preconditions

Use only the project VPS:

```text
ssh_target=mcpspain-official-sources-vps
ssh_user=root
host=157.90.22.40
app_path=/opt/official-sources/app
db_path=/opt/official-sources/data/official_sources.sqlite
cli=/opt/official-sources/app/.venv/bin/official-sources
```

Before running, confirm the deployed checkout contains the BOA adapter and this runbook:

```bash
ssh mcpspain-official-sources-vps
cd /opt/official-sources/app
git status --short
git rev-parse --short HEAD
/opt/official-sources/app/.venv/bin/official-sources --help | grep -F "ingest-boa-date"
```

Stop before any backfill command if:

- the remote worktree is dirty;
- `ingest-boa-date` is missing from `--help`;
- the deployed commit is not the approved commit for the run;
- database validation fails;
- a current pre-run backup cannot be created and verified.

## Adapter Facts Used By This Runbook

The BOA adapter reviewed for this runbook is metadata-only. It stores official document
metadata, the BOA official URLs as metadata, one `raw_api_response` document file row per
document, the source snapshot hash, and ingestion-run counters.

The official endpoint used by the adapter is:

```text
https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VERLST&BASE=BOLE&DOCS=1-250&SEC=OPENDATABOAJSONAPP&OUTPUTMODE=JSON&SORT=-PUBL&SEPARADOR=&PUBL=YYYYMMDD
```

Important limit risk:

- the request window is `DOCS=1-250`;
- the parser treats the returned array as complete;
- there is no pagination beyond `DOCS=1-250`;
- therefore `documents_fetched=250` means possible truncation and is a hard stop.

## Pre-Run Backup And Validation

Run these commands on the VPS before the loop:

```bash
set -euo pipefail

APP=/opt/official-sources/app
CLI=/opt/official-sources/app/.venv/bin/official-sources
DB=/opt/official-sources/data/official_sources.sqlite
BACKUP_DIR=/opt/official-sources/data/backups
LOG_DIR=/opt/official-sources/logs
STAMP=$(date +%Y%m%d_%H%M%S)

cd "$APP"
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

git status --short
git rev-parse --short HEAD
"$CLI" --help | grep -F "ingest-boa-date"
"$CLI" --db-path "$DB" db validate

"$CLI" --db-path "$DB" db backup \
  --output "$BACKUP_DIR/official_sources_before_boa_30d_backfill_${STAMP}.sqlite"
```

Record the full `db backup` output in the operational report. The backup is acceptable
only if it reports:

```text
verification=quick_check
source_check=ok
backup_check=ok
status=success
```

Capture pre-run counters:

```bash
sqlite3 "$DB" <<'SQL'
.headers on
.mode column
SELECT COUNT(*) AS boa_official_documents
FROM official_documents d
JOIN official_sources s ON s.id = d.source_id
WHERE s.code = 'BOA';

SELECT COUNT(*) AS boa_ingestion_runs
FROM ingestion_runs
WHERE source_code = 'BOA';

SELECT COUNT(*) AS source_candidates
FROM source_candidates;

SELECT COUNT(*) AS artifact_download_attempts
FROM artifact_download_attempts;

SELECT f.file_type, COUNT(*) AS count
FROM document_files f
JOIN official_documents d ON d.id = f.document_id
JOIN official_sources s ON s.id = d.source_id
WHERE s.code = 'BOA'
GROUP BY f.file_type
ORDER BY f.file_type;
SQL

du -sb /opt/official-sources/data/artifacts 2>/dev/null || true
```

## Backfill Command Loop

Run the loop exactly once. It stops on command failure, API-risk signals, pagination-limit
risk, retry/throttle risk, or missing source hashes.

```bash
set -euo pipefail

APP=/opt/official-sources/app
CLI=/opt/official-sources/app/.venv/bin/official-sources
DB=/opt/official-sources/data/official_sources.sqlite
LOG_DIR=/opt/official-sources/logs
DATE_FROM=2026-04-21
DATE_TO=2026-05-20
STAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/boa_30d_backfill_${STAMP}.log"

cd "$APP"
mkdir -p "$LOG_DIR"

python - <<'PY' | while read -r d; do
from datetime import date, timedelta
start = date.fromisoformat("2026-04-21")
end = date.fromisoformat("2026-05-20")
current = start
while current <= end:
    print(current.isoformat())
    current += timedelta(days=1)
PY
  echo "date_started=$d" | tee -a "$LOG"
  set +e
  output=$("$CLI" --db-path "$DB" ingest-boa-date --date "$d" 2>&1)
  rc=$?
  set -e
  printf '%s\n' "$output" | tee -a "$LOG"
  echo "date_finished=$d exit_code=$rc" | tee -a "$LOG"

  if [ "$rc" -ne 0 ]; then
    echo "STOP: ingest-boa-date exited non-zero for $d" | tee -a "$LOG"
    exit 1
  fi

  case "$output" in
    *"status=failed"*)
      echo "STOP: status=failed for $d" | tee -a "$LOG"
      exit 1
      ;;
  esac

  if ! printf '%s\n' "$output" | grep -q "last_http_status=200"; then
    echo "STOP: last_http_status is not 200 for $d" | tee -a "$LOG"
    exit 1
  fi

  if printf '%s\n' "$output" | grep -q "source_snapshot_hash=none"; then
    echo "STOP: missing source_snapshot_hash for $d" | tee -a "$LOG"
    exit 1
  fi

  fetched=$(printf '%s\n' "$output" | sed -n 's/.*documents_fetched=\([0-9][0-9]*\).*/\1/p' | tail -n 1)
  if [ "${fetched:-0}" -ge 250 ]; then
    echo "STOP: documents_fetched reached ${fetched:-unknown}; BOA DOCS=1-250 limit risk requires manual pagination review" | tee -a "$LOG"
    exit 1
  fi

  retry_count=$(printf '%s\n' "$output" | sed -n 's/.*retry_count=\([0-9][0-9]*\).*/\1/p' | tail -n 1)
  if [ "${retry_count:-0}" -gt 0 ]; then
    echo "STOP: retry_count=${retry_count:-unknown}; API limit or reliability risk requires review" | tee -a "$LOG"
    exit 1
  fi

  throttle_triggered=$(printf '%s\n' "$output" | sed -n 's/.*throttle_triggered=\([0-9][0-9]*\).*/\1/p' | tail -n 1)
  if [ "${throttle_triggered:-0}" -ne 0 ]; then
    echo "STOP: throttle_triggered=${throttle_triggered:-unknown}; API limit risk requires review" | tee -a "$LOG"
    exit 1
  fi

  sleep 1
done

echo "log_path=$LOG"
```

Expected log path pattern:

```text
/opt/official-sources/logs/boa_30d_backfill_YYYYMMDD_HHMMSS.log
```

## Stop Conditions

Stop immediately and do not resume without a new explicit task if any of these occur:

- any command exits non-zero;
- `status=failed`;
- `last_http_status` is not `200`;
- `source_snapshot_hash=none`;
- `documents_fetched` reaches `250`;
- any other sign that the BOA `DOCS=1-250` API limit may have truncated results;
- `retry_count` is greater than `0`;
- `throttle_triggered` is non-zero;
- repeated slow responses, timeout symptoms, HTTP 429/5xx, or operator-visible API pressure;
- candidate count changes;
- artifact download attempt count changes;
- BOA creates any `document_files.file_type` other than `raw_api_response`;
- database validation fails before or after the run;
- the loop processes a date outside `2026-04-21` through `2026-05-20`;
- a downstream, candidate, artifact download, or unrelated ingestion command is accidentally run.

If stopped because `documents_fetched=250`, do not mark the date as complete. The next task
must inspect BOA pagination/completeness behavior before any resume.

## Post-Run Validation

Run after the loop only if no stop condition fired:

```bash
set -euo pipefail

CLI=/opt/official-sources/app/.venv/bin/official-sources
DB=/opt/official-sources/data/official_sources.sqlite
BACKUP_DIR=/opt/official-sources/data/backups
STAMP=$(date +%Y%m%d_%H%M%S)

"$CLI" --db-path "$DB" db validate

sqlite3 "$DB" <<'SQL'
.headers on
.mode column
SELECT status, COUNT(*) AS count, COALESCE(SUM(documents_fetched), 0) AS documents_fetched
FROM ingestion_runs
WHERE source_code = 'BOA'
  AND target_date BETWEEN '2026-04-21' AND '2026-05-20'
GROUP BY status
ORDER BY status;

SELECT target_date, status, documents_fetched, documents_new, documents_updated,
       retry_count, throttle_triggered, last_http_status
FROM ingestion_runs
WHERE source_code = 'BOA'
  AND target_date BETWEEN '2026-04-21' AND '2026-05-20'
ORDER BY target_date, id;

SELECT COUNT(*) AS source_candidates
FROM source_candidates;

SELECT COUNT(*) AS artifact_download_attempts
FROM artifact_download_attempts;

SELECT f.file_type, COUNT(*) AS count
FROM document_files f
JOIN official_documents d ON d.id = f.document_id
JOIN official_sources s ON s.id = d.source_id
WHERE s.code = 'BOA'
GROUP BY f.file_type
ORDER BY f.file_type;

SELECT COUNT(*) AS boa_non_raw_api_response_files
FROM document_files f
JOIN official_documents d ON d.id = f.document_id
JOIN official_sources s ON s.id = d.source_id
WHERE s.code = 'BOA'
  AND f.file_type <> 'raw_api_response';
SQL

du -sb /opt/official-sources/data/artifacts 2>/dev/null || true

"$CLI" --db-path "$DB" db backup \
  --output "$BACKUP_DIR/official_sources_after_boa_30d_backfill_${STAMP}.sqlite"
```

Post-run acceptance checks:

- `db validate` reports `status=valid`;
- 30 BOA target dates were attempted, unless the report explicitly records a stop condition;
- no failed dates exist;
- no date has `documents_fetched >= 250`;
- all date rows have `last_http_status=200`;
- all date rows have `retry_count=0`;
- all date rows have `throttle_triggered=0`;
- `source_candidates` equals the pre-run count;
- `artifact_download_attempts` equals the pre-run count;
- BOA `document_files` contain only `raw_api_response`;
- artifact directory size is unchanged except for unrelated pre-existing state that must be
  explained in the report;
- post-run backup reports `verification=quick_check`, `source_check=ok`, `backup_check=ok`,
  and `status=success`.

## Report To Create After Execution

Expected operational report path:

```text
docs/reports/BOA_30_DAY_METADATA_BACKFILL_2026-05-23.md
```

That report must include:

- deployed commit hash;
- exact VPS host and app/database paths;
- exact date range;
- pre-run validation result;
- pre-run backup path and verification result;
- log path;
- per-date command output summary;
- success/no-publication/failed counts;
- total `documents_fetched`, `documents_new`, and `documents_updated`;
- maximum `documents_fetched` for any date and confirmation it never reached `250`;
- HTTP status, retry, and throttle summary;
- pre/post `source_candidates` count;
- pre/post `artifact_download_attempts` count;
- BOA `document_files` counts by `file_type`;
- pre/post artifact directory size;
- post-run validation result;
- post-run backup path and verification result;
- explicit statement that no artifacts, candidates, or downstream writes were performed.

## Readiness

This runbook is ready for a separately approved VPS execution of the BOA 30-day
metadata-only backfill. It is not approval to run the backfill.

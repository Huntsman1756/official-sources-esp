# BORM 30-Day Metadata Backfill Runbook - 2026-05-23

## Scope

Task: `TASK-AUTO-BORM-003-RUNBOOK`.

This runbook prepares the exact VPS procedure for a supervised BORM metadata-only
backfill. It does not authorize candidate creation, artifact downloads, downstream
writes, or historical expansion beyond the listed 30-day range.

Target VPS and paths:

```text
VPS: mcpspain-official-sources-vps / root@157.90.22.40
App path: /opt/official-sources/app
CLI: /opt/official-sources/app/.venv/bin/official-sources
Database: /opt/official-sources/data/official_sources.sqlite
Backups: /opt/official-sources/data/backups
Logs: /opt/official-sources/logs
```

Run only this command class:

```text
official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-borm-date --date YYYY-MM-DD
```

Do not chain or run:

```text
find-source-candidates
find-boe-candidates
download-boe-artifacts
download-source-artifacts
candidate-evidence-status
mark-candidate-evidence
export-reviewed-evidence
any downstream project command
```

## Evidence Reviewed

Reviewed local implementation and reports:

- `src/official_sources/sources/borm/client.py`
- `src/official_sources/sources/borm/parser.py`
- `src/official_sources/sources/borm/ingestion.py`
- `docs/reports/BORM_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/BORM_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/PREFLIGHT_AND_BOPV_BACKFILL_INTEGRATION_2026-05-23.md`

Adapter behavior:

- Fetches the official current-year XML index:
  `https://transparencia.carm.es/rest-services/services/restFile/BORMIndice.xml`.
- Filters records where `Fec_Publicacion` starts with the requested
  `YYYY-MM-DD`.
- Stores official document metadata and the raw XML index snapshot as
  `raw_api_response`.
- Preserves HTML/PDF official URLs as metadata only.
- Does not create `source_candidates`.
- Does not create `artifact_download_attempts`.
- Does not download PDF, HTML, or XML artifacts.
- Does not touch downstream evidence exports.

Preflight smoke result:

```text
2026-05-20: status=success, issue_identifier=114/2026, documents_fetched=41
2026-05-17: status=no_publication, documents_fetched=0
db validate: valid=True
source_candidates=0
artifact_download_attempts=0
pdf_files=0
raw_snapshots=41
```

## Target Range

Use this fixed range for the 2026-05-23 task:

```text
2026-04-24 through 2026-05-23 inclusive
30 dates
```

Do not replace the fixed range with `date.today()` or a moving 30-day window.
If the operation is delayed and the desired business range changes, produce a new
runbook or explicit operator note before execution.

## Current-Index And Historical-Range Risk

BORM currently uses a current-year XML index. That strategy is acceptable for the
May 2026 30-day window above because both preflight dates were in the same
current-year index.

This strategy is not acceptable for broad historical backfills, cross-year
backfills, or year-boundary windows unless archived annual BORM index resources
are first identified and implemented.

Operational implications:

- Do not run dates outside calendar year 2026 with the current adapter.
- Do not run a range that crosses 2026-12-31 / 2027-01-01.
- Stop if the current index no longer contains expected recent published dates.
- Expect repeated network fetches and repeated `raw_api_response` snapshots,
  because every date fetches the same current-year XML and filters locally.

## Pre-Run Requirements

Run this operation only when no other ingestion, artifact download, candidate,
MCP maintenance, or downstream export task is active against the same database.

Set variables:

```bash
cd /opt/official-sources/app

OFFICIAL_SOURCES=/opt/official-sources/app/.venv/bin/official-sources
DB=/opt/official-sources/data/official_sources.sqlite
BACKUP_DIR=/opt/official-sources/data/backups
LOG_DIR=/opt/official-sources/logs
STAMP=$(date -u +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/borm_30d_backfill_${STAMP}.log"
PRE_BACKUP="$BACKUP_DIR/official_sources_before_borm_30d_backfill_${STAMP}.sqlite"
POST_BACKUP="$BACKUP_DIR/official_sources_after_borm_30d_backfill_${STAMP}.sqlite"
```

Confirm CLI surface and clean deploy state:

```bash
git status --short
git rev-parse --short HEAD
"$OFFICIAL_SOURCES" --help | grep -q "ingest-borm-date"
```

Create a pre-run backup and validate the active DB:

```bash
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

"$OFFICIAL_SOURCES" --db-path "$DB" db backup --output "$PRE_BACKUP"
"$OFFICIAL_SOURCES" --db-path "$DB" db validate
```

Record pre-run counters:

```bash
python - <<'PY' | tee -a "$LOG"
import sqlite3

db = "/opt/official-sources/data/official_sources.sqlite"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

queries = {
    "borm_documents": """
        SELECT COUNT(*) AS value
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
    """,
    "borm_runs": """
        SELECT COUNT(*) AS value
        FROM ingestion_runs
        WHERE source_code = 'BORM'
    """,
    "source_candidates": "SELECT COUNT(*) AS value FROM source_candidates",
    "artifact_download_attempts": "SELECT COUNT(*) AS value FROM artifact_download_attempts",
    "borm_non_raw_file_rows": """
        SELECT COUNT(*) AS value
        FROM document_files f
        JOIN official_documents d ON d.id = f.document_id
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
          AND f.file_type <> 'raw_api_response'
    """,
    "borm_pdf_file_rows": """
        SELECT COUNT(*) AS value
        FROM document_files f
        JOIN official_documents d ON d.id = f.document_id
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
          AND f.file_type = 'pdf'
    """,
}

for label, query in queries.items():
    print(f"before_{label}={conn.execute(query).fetchone()['value']}")
PY

du -sb /opt/official-sources/data/artifacts | tee -a "$LOG"
```

Do not proceed unless:

- `db backup` reports success.
- `db validate` reports `status=valid`.
- `git status --short` is understood and does not contain unexpected local edits.
- `ingest-borm-date` is present in `--help`.
- Pre-run `source_candidates`, `artifact_download_attempts`, BORM non-raw file
  rows, BORM PDF rows, and artifact directory size have been recorded.

## Command Loop

Run the 30 dates serially, one date at a time:

```bash
set -o pipefail

cat > /tmp/borm_30d_dates.txt <<'EOF'
2026-04-24
2026-04-25
2026-04-26
2026-04-27
2026-04-28
2026-04-29
2026-04-30
2026-05-01
2026-05-02
2026-05-03
2026-05-04
2026-05-05
2026-05-06
2026-05-07
2026-05-08
2026-05-09
2026-05-10
2026-05-11
2026-05-12
2026-05-13
2026-05-14
2026-05-15
2026-05-16
2026-05-17
2026-05-18
2026-05-19
2026-05-20
2026-05-21
2026-05-22
2026-05-23
EOF

while read -r d; do
  echo "borm_backfill_date=$d started_at=$(date -u --iso-8601=seconds)" | tee -a "$LOG"
  "$OFFICIAL_SOURCES" --db-path "$DB" ingest-borm-date --date "$d" 2>&1 | tee -a "$LOG"
  rc=${PIPESTATUS[0]}
  if [ "$rc" -ne 0 ]; then
    echo "borm_backfill_stop date=$d exit_code=$rc" | tee -a "$LOG"
    exit "$rc"
  fi
  sleep 1
done < /tmp/borm_30d_dates.txt
```

The expected successful date output class is:

```text
command_started=ingest-borm-date source_code=BORM target_date=YYYY-MM-DD
status=success ... documents_fetched=N ... last_http_status=200 ...
```

The expected no-publication output class is:

```text
command_started=ingest-borm-date source_code=BORM target_date=YYYY-MM-DD
status=no_publication ... documents_fetched=0 ... last_http_status=200 ...
```

## Post-Run DB Validation

Validate the database immediately after the loop:

```bash
"$OFFICIAL_SOURCES" --db-path "$DB" db validate | tee -a "$LOG"
```

Run the summary and safety checks:

```bash
python - <<'PY' | tee -a "$LOG"
import sqlite3

db = "/opt/official-sources/data/official_sources.sqlite"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

print("borm_runs_in_target_range")
for row in conn.execute("""
    SELECT target_date, status, documents_fetched, documents_new,
           documents_updated, last_http_status, retry_count, throttle_triggered,
           error_message
    FROM ingestion_runs
    WHERE source_code = 'BORM'
      AND target_date BETWEEN '2026-04-24' AND '2026-05-23'
    ORDER BY target_date
"""):
    print(dict(row))

queries = {
    "after_borm_documents": """
        SELECT COUNT(*) AS value
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
    """,
    "after_borm_target_range_documents": """
        SELECT COUNT(*) AS value
        FROM official_documents d
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
          AND d.publication_date BETWEEN '2026-04-24' AND '2026-05-23'
    """,
    "after_borm_runs": """
        SELECT COUNT(*) AS value
        FROM ingestion_runs
        WHERE source_code = 'BORM'
    """,
    "after_borm_target_range_runs": """
        SELECT COUNT(*) AS value
        FROM ingestion_runs
        WHERE source_code = 'BORM'
          AND target_date BETWEEN '2026-04-24' AND '2026-05-23'
    """,
    "after_borm_target_range_failed_runs": """
        SELECT COUNT(*) AS value
        FROM ingestion_runs
        WHERE source_code = 'BORM'
          AND target_date BETWEEN '2026-04-24' AND '2026-05-23'
          AND status = 'failed'
    """,
    "after_borm_target_range_non_200_runs": """
        SELECT COUNT(*) AS value
        FROM ingestion_runs
        WHERE source_code = 'BORM'
          AND target_date BETWEEN '2026-04-24' AND '2026-05-23'
          AND COALESCE(last_http_status, 0) <> 200
    """,
    "after_source_candidates": "SELECT COUNT(*) AS value FROM source_candidates",
    "after_artifact_download_attempts": "SELECT COUNT(*) AS value FROM artifact_download_attempts",
    "after_borm_non_raw_file_rows": """
        SELECT COUNT(*) AS value
        FROM document_files f
        JOIN official_documents d ON d.id = f.document_id
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
          AND f.file_type <> 'raw_api_response'
    """,
    "after_borm_pdf_file_rows": """
        SELECT COUNT(*) AS value
        FROM document_files f
        JOIN official_documents d ON d.id = f.document_id
        JOIN official_sources s ON s.id = d.source_id
        WHERE s.code = 'BORM'
          AND f.file_type = 'pdf'
    """,
}

for label, query in queries.items():
    print(f"{label}={conn.execute(query).fetchone()['value']}")
PY

du -sb /opt/official-sources/data/artifacts | tee -a "$LOG"
```

Create the post-run backup only after `db validate` reports `status=valid` and
the safety counters are acceptable:

```bash
"$OFFICIAL_SOURCES" --db-path "$DB" db backup --output "$POST_BACKUP"
```

## Required Acceptance Criteria

The run is acceptable only if all are true:

- Exactly 30 target dates were attempted.
- Each target date has latest BORM output with `status=success` or
  `status=no_publication`.
- No target date has `status=failed`.
- Every target date has `last_http_status=200`.
- `db validate` reports `status=valid` before and after the loop.
- `source_candidates` count is unchanged.
- `artifact_download_attempts` count is unchanged.
- BORM non-`raw_api_response` file row count is unchanged.
- BORM PDF file row count is unchanged.
- Artifact directory size is unchanged.
- Post-run backup succeeds after validation.

Review manually before accepting:

- Any normal weekday with `status=no_publication`.
- Any unexpectedly high or low `documents_fetched` count.
- Any repeated `retry_count > 0` or `throttle_triggered > 0`.
- Any evidence that the XML index has stopped representing the current year.

## Stop Conditions

Stop immediately and report without continuing the range if any of these occur:

- Pre-run backup fails or cannot be verified.
- Pre-run `db validate` is not `status=valid`.
- `ingest-borm-date` is missing from the deployed CLI.
- Any date command exits non-zero.
- Any date returns `status=failed`.
- Any date has `last_http_status` other than `200`.
- XML parsing fails or required BORM fields are missing.
- The parser reports mixed issue identifiers for one target date.
- A recent expected publication date returns zero records without manual calendar
  explanation.
- `source_candidates` count changes.
- `artifact_download_attempts` count changes.
- Any BORM `document_files.file_type` other than `raw_api_response` appears.
- Any BORM PDF file row appears.
- Artifact directory size changes.
- Any downstream file/export is touched.
- The operator cannot reconcile sampled BORM counts against the official website.

If a stop condition fires after some dates have already run, do not retry in a
new loop until the partial state is documented with:

- last successful date;
- failed/blocked date;
- latest `db validate` output;
- current safety counters;
- whether a post-failure backup was created.

## Artifact, Candidate, And Downstream Safety

BORM metadata ingestion may add:

```text
official_sources row for BORM, if missing
official_documents rows for BORM
document_files rows with file_type=raw_api_response
ingestion_runs rows for BORM
```

BORM metadata ingestion must not add or modify:

```text
source_candidates
artifact_download_attempts
PDF/HTML/XML downloaded artifact files
candidate_evidence_reviews
downstream evidence JSON
downstream benefit/content files
```

The presence of BORM `url_html` and `url_pdf` values in document metadata is not
an artifact download. It is acceptable only as stored official metadata.

## Sequencing Against BOA And DOGC

BORM should be attempted before BOA and DOGC if the next decision is to expand
autonomous metadata coverage with one additional 30-day VPS backfill.

Reason:

- BORM has a clean published-date and no-publication preflight.
- BORM has no first-page pagination ceiling like BOA or DOGC for this current
  30-day window.
- BORM's main risk is the current-year index strategy, and that risk is bounded
  by the fixed May 2026 range.
- BOA is also viable, but it must stop on `documents_fetched=250` because the
  current request uses `DOCS=1-250` without pagination.
- DOGC should wait for a VPS single-date live smoke because local live probing
  hit a TLS handshake failure and the adapter currently uses page 1 with
  `numResultsByPage=100`.

Do not run BORM, BOA, and DOGC in parallel. Keep VPS backfills serial and keep
candidate dry-runs separate from metadata backfills.

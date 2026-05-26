# VPS Service Drift Diagnosis - 2026-05-26

## Scope

This report diagnoses the VPS drift observed before opening `TASK-SOURCE-RSS-MONITOR-001`.

Target services:

- `official-sources-boe-daily.service`
- `official-sources-integrity-check.service`

Hard boundary:

- No application code was changed on the VPS.
- `/opt/official-sources/app` was not modified.
- `/opt/official-sources/auditor-app` was not modified.
- No downstream databases, candidates, evidence-grade records, broad backfills, or Hermes units were touched.

## Commands Run

```bash
systemctl status official-sources-boe-daily.service --no-pager
systemctl status official-sources-integrity-check.service --no-pager
journalctl -u official-sources-boe-daily.service -n 200 --no-pager
journalctl -u official-sources-integrity-check.service -n 200 --no-pager
systemctl cat official-sources-boe-daily.service
systemctl cat official-sources-integrity-check.service
ls -ld /opt/official-sources/data/artifacts/boe
ls -ld /opt/official-sources/data/artifacts/boe/2026
ls -ld /opt/official-sources/data/artifacts/boe/2026/05
cd /opt/official-sources/app && git status --short && git branch --show-current && git log -1 --oneline
cd /opt/official-sources/auditor-app && git status --short && git branch --show-current && git log -1 --oneline
chown -R official-sources:official-sources /opt/official-sources/data/artifacts/boe/2026
systemctl reset-failed official-sources-boe-daily.service official-sources-integrity-check.service
systemctl start official-sources-boe-daily.service
systemctl start official-sources-integrity-check.service
cd /opt/official-sources/app && set -a && . /opt/official-sources/.env && set +a
/opt/official-sources/app/.venv/bin/python - <<'PY'
import os, sqlite3
from pathlib import Path
from collections import Counter

conn = sqlite3.connect(os.environ["OFFICIAL_SOURCES_DB_PATH"])
conn.row_factory = sqlite3.Row
rows = conn.execute("""
SELECT f.id, f.file_type, f.local_path, f.official_url, d.external_id
FROM document_files f JOIN official_documents d ON d.id=f.document_id
WHERE d.publication_date='2026-05-26'
ORDER BY f.id
""").fetchall()
missing = [r for r in rows if not r["local_path"] or not Path(r["local_path"]).exists()]
print("total", len(rows))
print("by_type", dict(Counter(r["file_type"] for r in rows)))
print("missing", len(missing), dict(Counter(r["file_type"] for r in missing)))
PY
cd /opt/official-sources/app && set -a && . /opt/official-sources/.env && set +a && \
  /opt/official-sources/app/.venv/bin/official-sources status --date today
cd /opt/official-sources/app && set -a && . /opt/official-sources/.env && set +a && \
  /opt/official-sources/app/.venv/bin/official-sources db validate
systemctl --failed --no-pager
systemctl list-timers official-sources-boe-daily.timer official-sources-integrity-check.timer official-sources-hermes-auditor.timer --no-pager
```

One manual status command was initially run without loading `/opt/official-sources/.env`, which created a default `/root/official-sources.sqlite`. That incidental file was removed immediately:

```bash
rm -f /root/official-sources.sqlite
```

## Service Definitions

Both units run as `official-sources:official-sources`, use `WorkingDirectory=/opt/official-sources/app`, load `/opt/official-sources/.env`, and execute `/opt/official-sources/app/.venv/bin/official-sources`.

`official-sources-boe-daily.service` runs:

```text
ingest-boe-summary --date today
download-boe-artifacts --date today --types xml,html
status --date today
```

`official-sources-integrity-check.service` runs:

```text
integrity-check --date today
status --date today
```

## Current Status

### `official-sources-boe-daily.service`

Status after the safe operational fix: resolved.

Observed successful run:

```text
status=success documents_fetched=175 documents_new=0 documents_updated=175 last_http_status=200
selected_documents=175 artifact_types=xml,html downloaded=350 failed=0
ingestion_status=success last_http_status=200 xml_files=175 html_files=175 pdf_files=0 integrity_warnings=0 failed_downloads=0
```

Root cause:

```text
permission issue
```

The service user could write under `/opt/official-sources/data/artifacts/boe`, but the year/month subtree for 2026 had drifted to `root:root` ownership. The failing logs showed repeated permission errors writing under:

```text
/opt/official-sources/data/artifacts/boe/2026/05/26
```

Operational fix applied:

```bash
chown -R official-sources:official-sources /opt/official-sources/data/artifacts/boe/2026
systemctl reset-failed official-sources-boe-daily.service official-sources-integrity-check.service
systemctl start official-sources-boe-daily.service
```

Validation:

- The 2026 artifact directories are now owned by `official-sources:official-sources`.
- The BOE daily service completed successfully.
- The 2026-05-26 artifact directory contains the expected XML/HTML files for the daily run.

### `official-sources-integrity-check.service`

Status after BOE artifact repair: still failing.

Observed run:

```text
unchanged=350 changed=0 missing=175
```

Database check for `2026-05-26`:

```text
total 525
by_type {'raw_api_response': 175, 'xml': 175, 'html': 175}
missing 175 {'raw_api_response': 175}
```

Classification:

```text
command/API behavior changed
```

Best-supported hypothesis:

`integrity-check --date today` iterates every `document_files` row for the date. It treats rows with `local_path = NULL` as missing local files. Current BOE ingestion creates `raw_api_response` rows for the summary/API metadata and these rows are valid metadata/hash records, not local artifact files. The integrity check therefore fails on expected non-local metadata records while correctly validating the 350 local XML/HTML artifacts as unchanged.

This is not currently supported as a safe operational-only fix. It should be handled as a separate code task by clarifying the integrity-check contract. Likely fix shape:

- skip `document_files` rows where `local_path IS NULL`, or
- filter the command to local artifact file types only, or
- add an explicit CLI option separating local artifact integrity from raw metadata hash records.

Do not delete `raw_api_response` rows to make the service green.

## Productive Checkout State

Productive checkout:

```text
path=/opt/official-sources/app
branch=main
commit=0878b96 docs: add oposiciones alert scope dry-run report
git_status=clean
```

Auditor checkout:

```text
path=/opt/official-sources/auditor-app
branch=codex/task-source-registry-001
commit=9e7f6bb chore(hermes): add local and VPS audit fleet
git_status=clean
```

## Hermes Impact

Hermes is not affected by either failure.

Current separation remains intact:

- Hermes service/timer was not changed.
- Hermes uses `/opt/official-sources/auditor-app`, not the productive checkout.
- `official-sources-hermes-auditor.timer` remains scheduled separately.

## Database And Runtime Validation

With `/opt/official-sources/.env` loaded, the productive database validates:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

The manual command run without the systemd environment was discarded as invalid evidence and its incidental default SQLite file was removed.

## Recommended Fix

1. Leave the BOE artifact ownership repair in place.
2. Open a separate bounded task for `integrity-check` semantics before treating the VPS systemd baseline as fully green.
3. Do not change or disable Hermes.
4. Do not delete `raw_api_response` records.
5. Do not mix the integrity-check fix with `TASK-SOURCE-RSS-MONITOR-001`.

Suggested follow-up task:

```text
TASK-VPS-INTEGRITY-CHECK-RAW-METADATA-001
```

Goal:

```text
Make local artifact integrity checks ignore or separately classify non-local raw metadata records with local_path=NULL, preserving raw_api_response provenance and keeping missing real artifacts as failures.
```

## RSS Monitor Blocker Decision

`TASK-SOURCE-RSS-MONITOR-001` should not absorb this VPS repair.

The infrastructure drift is now classified:

- BOE daily: repaired operationally.
- Integrity service: known separate command-contract bug.
- Hermes: unaffected.
- Productive checkout: not modified.

RSS monitor work can proceed as a separate metadata-only branch only if the red integrity service is tracked as its own task and not used as evidence that RSS broke production.

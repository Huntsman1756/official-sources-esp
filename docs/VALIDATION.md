# Validation

## Commands Executed

TASK-004C local validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `175 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- Focused TASK-004C tests covered no-publication payload behavior, controlled range ingestion,
  range safety limits, local candidate prefiltering, structured cache misses, and separated
  summary/artifact status output.

TASK-004A-FIX2 local validation:

```bash
rtk python -m pytest tests/test_cli.py -q
rtk python -m ruff check src/official_sources/cli.py src/official_sources/storage/repository.py tests/test_cli.py
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Focused tests: `20 passed`.
- Focused lint: `All checks passed!`.
- Full tests: `155 passed`.
- Full lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- Status output now reports `summary_*` fields separately from `artifact_*` fields.
- Artifact HTTP summaries are read from `artifact_download_attempts`.
- Legacy `ingestion_status` and `last_http_status` remain summary aliases for compatibility.

TASK-004A-FIX1 local validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `152 passed`.
- Lint: `All checks passed!`.
- Formatting: `56 files already formatted`.
- New schema latest version: `6`.
- Focused no-publication behavior tests: BOE summary `404` persists `last_http_status=404`, records `status=no_publication`, exits zero from the CLI, skips artifact download, and keeps real 500/malformed-200 failures as `failed`.

TASK-004A-FIX1 VPS validation:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db backup --output /opt/official-sources/data/backups/official_sources_before_no_publication_fix_20260517_173237.sqlite
git pull --ff-only origin main
python -m pip install -e .
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db status
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db migrate
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
systemctl start official-sources-boe-daily.service
systemctl status official-sources-boe-daily.service --no-pager --full
journalctl -u official-sources-boe-daily.service -n 300 --no-pager
official-sources --db-path /opt/official-sources/data/official_sources.sqlite status --date today
```

Result:

- Pre-update backup: `verification=quick_check source_check=ok backup_check=ok status=success`.
- Deployed commit: `a942899`.
- Migration: `current_version=6 latest_version=6 applied_migrations=6 status=migrated`.
- VPS DB validation: `current_version=6 latest_version=6 status=valid`.
- Forced BOE daily service: `service_start_exit=0`.
- systemd result: all three `ExecStart` commands ended with `status=0/SUCCESS`.
- Today status: `ingestion_status=no_publication last_http_status=404 documents=0 ... failed_downloads=0`.
- Artifact directory remained empty apart from the directory itself.
- MCP privacy remained intact: no MCP/FastMCP/Python/Uvicorn listener.

TASK-004A real VPS deployment rehearsal:

```bash
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'set -eu; whoami; hostname -f; date -Is; cat /etc/os-release | head -n 5; uname -a; command -v python3.12; command -v git; systemctl --version | head -n 1'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'mkdir -p /opt/official-sources/app /opt/official-sources/data/artifacts /opt/official-sources/data/backups /opt/official-sources/logs'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'useradd --system --home /opt/official-sources --shell /usr/sbin/nologin official-sources 2>/dev/null || true'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'chown -R official-sources:official-sources /opt/official-sources'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'sudo -u official-sources git clone https://github.com/Huntsman1756/official-sources-esp.git /opt/official-sources/app'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'cd /opt/official-sources/app; sudo -u official-sources python3.12 -m venv .venv; sudo -u official-sources .venv/bin/python -m pip install --upgrade pip; sudo -u official-sources .venv/bin/python -m pip install -e .; sudo -u official-sources .venv/bin/official-sources --help'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'CLI=/opt/official-sources/app/.venv/bin/official-sources; DB=/opt/official-sources/data/official_sources.sqlite; sudo -u official-sources $CLI --db-path $DB db status; sudo -u official-sources $CLI --db-path $DB db migrate; sudo -u official-sources $CLI --db-path $DB db validate'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'CLI=/opt/official-sources/app/.venv/bin/official-sources; DB=/opt/official-sources/data/official_sources.sqlite; BACKUP=/opt/official-sources/data/backups/official_sources_20260517_170440.sqlite; sudo -u official-sources $CLI --db-path $DB db backup --output $BACKUP; cp $BACKUP /tmp/official_sources_restore_test.sqlite; chown official-sources:official-sources /tmp/official_sources_restore_test.sqlite; sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db status; sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db migrate; sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db validate'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'cd /opt/official-sources/app; cp deploy/systemd/official-sources-boe-daily.service /etc/systemd/system/; cp deploy/systemd/official-sources-boe-daily.timer /etc/systemd/system/; cp deploy/systemd/official-sources-integrity-check.service /etc/systemd/system/; cp deploy/systemd/official-sources-integrity-check.timer /etc/systemd/system/; systemctl daemon-reload; systemctl enable official-sources-boe-daily.timer official-sources-integrity-check.timer; systemctl start official-sources-boe-daily.timer official-sources-integrity-check.timer'
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> 'systemctl start official-sources-integrity-check.service; systemctl --no-pager --full status official-sources-integrity-check.service; journalctl -u official-sources-integrity-check.service -n 50 --no-pager'
```

Result:

- VPS access: successful as `root`.
- Environment: Ubuntu 24.04.4 LTS, Python 3.12, git, systemd 255.
- Application path: `/opt/official-sources/app`.
- Deployed commit: `c5b6350`.
- Package installation: `python -m pip install -e .` succeeded.
- CLI help printed successfully on the VPS.
- Database: migrated to `current_version=5 latest_version=5`.
- Database validation: `status=valid`.
- Backup: verified backup created at `/opt/official-sources/data/backups/official_sources_20260517_170440.sqlite`.
- Restore rehearsal: `/tmp/official_sources_restore_test.sqlite` status/migrate/validate passed.
- Smoke check: `status --date today` returned no documents and no failed downloads.
- systemd: both timers enabled and active.
- systemd smoke: `official-sources-integrity-check.service` ran with `status=0/SUCCESS`.
- MCP privacy: no MCP process, no `official-sources` listener, no public listener beyond SSH.
- Live BOE daily ingestion was not manually started; it is scheduled by timer.

TASK-004A dry-run after TASK-003F:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --help
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources.sqlite db backup --output G:/tmp/official-sources-task004a-20260517/backups/official_sources_20260517_000000.sqlite
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a-20260517/official_sources_restore_test.sqlite --artifact-dir G:/tmp/official-sources-task004a-20260517/artifacts status --date today
```

Result:

- Preflight tests: `144 passed`.
- Lint: `All checks passed!`.
- Formatting: `55 files already formatted`.
- CLI help printed successfully from the source entry point.
- New temporary DB status: `current_version=0 latest_version=5 pending_migrations=5 status=pending`.
- Migration: `current_version=5 latest_version=5 applied_migrations=1,2,3,4,5 status=migrated`.
- Validation: `current_version=5 latest_version=5 status=valid`.
- Verified backup: `verification=quick_check source_check=ok backup_check=ok size_bytes=110592 status=success`.
- Restore copy status: `current_version=5 latest_version=5 pending_migrations=0 status=up_to_date`.
- Restore copy migration: `applied_migrations=none status=up_to_date`.
- Restore copy validation: `current_version=5 latest_version=5 status=valid`.
- No-network status smoke check for `2026-05-17`: `ingestion_status=none documents=0 ... failed_downloads=0`.

TASK-003F red validation:

```bash
rtk python -m pytest tests\test_boe_http_policy.py tests\test_boe_artifacts.py tests\test_cli.py tests\test_sqlite_backup.py tests\test_security_docs.py tests\test_downstream_contract.py -q
```

Result: failed during collection because `official_sources.sources.boe.http_policy` did not exist yet. This was the expected red step for the new BOE runtime policy.

TASK-003F focused validation:

```bash
rtk python -m pytest tests\test_boe_http_policy.py tests\test_boe_artifacts.py tests\test_cli.py tests\test_sqlite_backup.py tests\test_storage_migrations.py tests\test_security_docs.py tests\test_downstream_contract.py -q
```

Result: `64 passed`.

TASK-003F full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `144 passed`.
- Lint: `All checks passed!`.
- Formatting: `55 files already formatted`.

TASK-004A preflight validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `123 passed in 1.92s`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-004A local CLI and database dry-run:

```bash
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --help
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources.sqlite db backup --output G:/tmp/official-sources-task004a/backups/official_sources_20260517_000000.sqlite
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite db status
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite db migrate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite db validate
rtk python -c "import sys; sys.path.insert(0, 'src'); from official_sources.cli import main; main()" --db-path G:/tmp/official-sources-task004a/official_sources_restore_test.sqlite --artifact-dir G:/tmp/official-sources-task004a/artifacts status --date today
```

Result:

- CLI help printed successfully from the source entry point.
- New temporary DB status: `current_version=0 latest_version=4 pending_migrations=4 status=pending`.
- Migration: `applied_migrations=1,2,3,4 status=migrated`.
- Validation: `current_version=4 latest_version=4 status=valid`.
- Backup: `pages=26 status=success`.
- Restore copy status: `current_version=4 latest_version=4 pending_migrations=0 status=up_to_date`.
- Restore copy migration: `applied_migrations=none status=up_to_date`.
- Restore copy validation: `current_version=4 latest_version=4 status=valid`.
- No-network status smoke check for `2026-05-17`: `ingestion_status=none documents=0 ... failed_downloads=0`.

TASK-004A focused validation:

```bash
rtk python -m pytest tests\test_mcp_tools.py tests\test_systemd_templates.py -q
```

Result: `11 passed in 0.23s`.

TASK-004A final validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `125 passed`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-003E validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `123 passed`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-003D red test run:

```bash
rtk python -m pytest tests\test_sqlite_backup.py -q
```

Result: failed during collection because `official_sources.storage.backup` did not exist yet. This was the expected red step.

TASK-003D focused test run:

```bash
rtk python -m pytest tests\test_sqlite_backup.py -q
```

Result: `8 passed`.

TASK-003D full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `123 passed`.
- Lint: `All checks passed!`.
- Formatting: `50 files already formatted`.

TASK-003C red test run:

```bash
rtk python -m pytest tests\test_storage_migrations.py tests\test_cli_db.py -q
```

Result: failed during collection because `official_sources.storage.migrations` did not exist yet. This was the expected red step.

TASK-003C focused test run:

```bash
rtk python -m pytest tests\test_storage_migrations.py tests\test_cli_db.py -q
```

Result: `16 passed`.

TASK-003C full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `115 passed`.
- Lint: `All checks passed!`.
- Formatting: `48 files already formatted`.

TASK-003B red test run:

```bash
rtk python -m pytest tests\test_boe_consolidated.py tests\test_cli_consolidated.py tests\test_mcp_consolidated.py tests\test_citation.py -q
```

Result: failed during collection because the consolidated index/block parser and block ID validator did not exist yet. This was the expected red step.

TASK-003B focused test run:

```bash
rtk python -m pytest tests\test_boe_consolidated.py tests\test_cli_consolidated.py tests\test_mcp_consolidated.py tests\test_citation.py -q
```

Result: `42 passed`.

TASK-003B full validation:

```bash
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

- Tests: `99 passed`.
- Lint: `All checks passed!`.
- Formatting: `40 files already formatted`.

Initial red test run:

```bash
python -m pytest -q
```

Result: failed because the `official_sources` package did not exist yet. This was the expected red step.

TASK-001 implementation test run:

```bash
python -m pytest -q
```

Result: `30 passed`.

TASK-002 red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py -q
```

Result: failed because `official_sources.sources.boe.artifacts` did not exist yet. This was the expected red step.

TASK-002 focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py -q
```

Result: `11 passed`.

TASK-002B red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_cli.py -q
```

Result: failed because `official_sources.cli` did not exist yet. This was the expected red step.

TASK-002B focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_cli.py -q
```

Result: `9 passed`.

TASK-002C red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py tests/test_cli.py tests/test_systemd_templates.py -q
```

Result: failed because `artifact_download_attempts`, real failed download counts, `today` date support, and systemd templates did not exist yet. This was the expected red step.

TASK-002C focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_artifacts.py tests/test_cli.py tests/test_systemd_templates.py -q
```

Result: `29 passed`.

TASK-003 red test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_consolidated.py tests/test_cli_consolidated.py tests/test_mcp_consolidated.py -q
```

Result: failed because consolidated legislation parser, storage, citation, CLI, and MCP tools did not exist yet. This was the expected red step.

TASK-003 focused test run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_boe_consolidated.py tests/test_cli_consolidated.py tests/test_mcp_consolidated.py -q
```

Result: `17 passed`.

Final test run, with bytecode writes disabled to avoid generated cache files:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

Result: `76 passed`.

Lint:

```bash
RUFF_CACHE_DIR=G:/tmp/official-sources-ruff-cache python -m ruff check .
```

Result: `All checks passed!`

Format check:

```bash
RUFF_CACHE_DIR=G:/tmp/official-sources-ruff-cache python -m ruff format --check .
```

Result: `40 files already formatted`.

## Corrections During Validation

An intermediate `ruff` run found line-length and import-order issues. They were corrected with:

```bash
python -m ruff check . --fix
python -m ruff format .
```

After those corrections, the final validation commands passed.

TASK-002 intermediate validation also found line-length/format issues in the new artifact files. They were corrected with the same Ruff commands before final validation.

TASK-002B intermediate validation found import-order and formatting issues in the new CLI files. They were corrected with Ruff before final validation.

TASK-002C intermediate validation found import-order and formatting issues in the new audit and CLI changes. They were corrected with Ruff before final validation.

The final Ruff commands used an explicit cache directory under `G:/tmp` to avoid a local `.ruff_cache` permission warning. The commands exited successfully.

TASK-003 intermediate validation found one expected MCP tool-name regression test and formatting issues in the new consolidated legislation files. They were corrected before final validation.

TASK-003B intermediate validation found one MCP tool-name expectation that needed the new index and block tools, plus one formatting issue in `tests/test_boe_consolidated.py`. They were corrected before final validation.

TASK-003C intermediate validation found style and formatting issues in the new migration files and migration tests. They were corrected before final validation.

TASK-003D intermediate validation found style and formatting issues in the new backup module and smoke tests. They were corrected before final validation.

## Test Coverage Summary

Tests cover:

- BOE date validation.
- BOE fixture parsing.
- Official source creation.
- Document normalization.
- Citation generation.
- Citation/integrity separation.
- Deterministic artifact hashes.
- Raw-payload source snapshot hashes.
- Default signature status.
- Hash-change audit events.
- Mandatory ingestion runs, including failures.
- Candidate human-review defaults.
- MCP snake_case tool names.
- Structured MCP text envelopes.
- Instruction-like legal text containment.
- MCP integrity read access without mutation.
- No protected table writes from MCP tools.
- XML artifact download from mocked BOE URL.
- HTML artifact download from mocked BOE URL.
- PDF artifact download from mocked BOE URL.
- BOE artifact URL validation.
- Raw-byte artifact hashes and source snapshot hashes.
- Local cache paths for downloaded artifacts.
- Unchanged artifact integrity checks.
- Changed artifact integrity checks.
- MCP tools do not perform artifact downloads.
- XML/HTML extracted official text remains wrapped in structured MCP output.
- CLI help.
- CLI date validation.
- CLI BOE summary ingestion using fixture fetcher.
- CLI XML/HTML/PDF artifact download using mocked HTTP.
- CLI rejection of non-BOE artifact URLs.
- CLI local integrity checks for unchanged and changed cached artifacts.
- CLI status counts.
- CLI separation from MCP and external project mutation.
- Artifact download attempt audit rows for XML, HTML, and PDF.
- Failed artifact download audit rows with HTTP status when available.
- Rejected non-BOE URLs create a failed audit signal without unsafe fetching.
- Real failed download counts in CLI status.
- Separation between `artifact_download_attempts` and `integrity_checks`.
- `today` date support for timer-friendly CLI runs.
- systemd template existence and safety checks.
- Consolidated BOE identifier validation.
- Consolidated law XML metadata parsing from fixture.
- Consolidated law raw payload hash before parsing.
- Consolidated law storage, version storage, and text block storage.
- Consolidated law citation and block citation.
- Consolidated law payload hash-change integrity events.
- CLI consolidated-law retrieval with mocked HTTP.
- MCP consolidated-law metadata, text envelope, and citation tools.
- Prompt-injection-like consolidated text containment.
- No consolidated-law search stub.
- No legal interpretation or version diffing in MCP tools.
- Consolidated law safe block ID validation.
- Consolidated law text index fixture parsing.
- Nested consolidated law text index hierarchy preservation.
- Consolidated text index raw payload hashing before parsing.
- Consolidated text index source snapshot hash storage.
- Consolidated law official block endpoint fixture parsing.
- Consolidated block raw payload hashing before parsing.
- Consolidated block source snapshot hash storage.
- Consolidated block content storage.
- Consolidated block payload hash-change previous-hash preservation.
- Consolidated block payload hash-change integrity event creation.
- CLI consolidated text index retrieval with mocked HTTP.
- CLI consolidated text block retrieval with mocked HTTP.
- CLI consolidated block retrieval rejection for unsafe block IDs.
- CLI consolidated block content output only with explicit `--print-content`.
- MCP consolidated text index structured output.
- MCP consolidated block required structured envelope.
- MCP consolidated block citation output.
- Prompt-injection-like consolidated block text containment inside `content`.
- No downstream project writes from MCP tools.
- Empty SQLite database migration to the latest schema.
- Upgrade from a 0001-style initial schema to the latest schema.
- Upgrade from a database before `artifact_download_attempts`.
- Upgrade from a database before consolidated legislation tables.
- Upgrade from a database before consolidated block endpoint fields.
- Preservation of existing `official_documents`, `document_files`, `ingestion_runs`, and consolidated law block content during migrations.
- Fresh migrated schema equivalence with the canonical latest schema columns.
- Migration checksum recording.
- Idempotent re-run behavior without duplicate migration rows.
- Detection of applied migration checksum mismatch.
- Failed migration not marked as applied.
- `db status` version and pending migration reporting.
- `db migrate` application and up-to-date reporting.
- `db validate` valid and invalid database reporting.
- Rejection of directory paths as SQLite database paths for `db` commands.
- SQLite backup creation through the online backup API.
- Backup overwrite rejection unless `--force` is explicit.
- Backup readability with `PRAGMA integrity_check`.
- Restored backup opened from a temporary path.
- Restored realistic pre-latest database migrated to the latest schema.
- Restored database validation after migration.
- Representative data preservation after restore and migration.
- Read-only status, document citation, consolidated block citation, and MCP block envelope after restore and migration.
- CLI `db backup` help, success output, overwrite rejection, and explicit `--force`.
- Backup module does not use network clients, BOE APIs, MCP tools, or downstream write paths.

## Known Limitations

- Live BOE network calls were not used in tests.
- XML/HTML/PDF artifact download is controlled by stored BOE document URLs.
- Electronic signature validation is not implemented.
- PDF text extraction is not implemented.
- systemd files are templates only and are not installed by this repository.
- BOE consolidated legislation search is future work.
- BOE consolidated legal version comparison is not implemented.
- BOE consolidated text index and block tests use fixtures and mocked HTTP, not live BOE network access.
- BOE consolidated block retrieval stores official endpoint snapshots but does not determine legal applicability.
- SQLite migrations are lightweight Python migrations, not Alembic or ORM migrations.
- PostgreSQL migrations are not implemented.
- The migration CLI does not create backups; operators must create a backup before migrating persistent installations.
- Automatic restore over the active database is not implemented.
- Cloud backups, encryption, compression, and backup rotation are not implemented.
- TASK-003E added operational documentation and ADRs only; no new adapters, endpoints, deployment automation, RAG, downstream integrations, or legal interpretation were implemented.

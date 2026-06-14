# DOCM Artifact Integrity Enrichment

Task: `TASK-OFFICIAL-SOURCES-DOCM-ARTIFACT-INTEGRITY-ENRICHMENT-001`

Date: 2026-06-14

## Scope

Add DOCM artifact integrity support to the existing metadata materialization path.

The task stays inside upstream parser/storage coverage:

- source: `DOCM` only;
- command: `ingest-monitor-date`;
- artifact kind: monitor summary HTML snapshot stored as `raw_api_response`;
- no candidate creation;
- no evidence-grade promotion;
- no downstream EduBecas writes;
- no VPS SQLite mutation;
- no runtime, systemd, timer, cap, or Hermes changes.

## Implementation

`monitor_html_source` now carries the fetched raw HTML payload in `HTMLParseResult.raw_page`.

When `ingest-monitor-date --source DOCM` materializes monitor records, it persists that official
summary HTML payload through `OfficialSourcesRepository.upsert_document_file`:

```text
file_type=raw_api_response
media_type=text/html
official_url=<DOCM date-scoped summary URL>
sha256=<raw HTML sha256>
source_snapshot_hash=<record raw_page_hash>
```

The repository still creates the integrity check row through the existing `upsert_document_file`
path.

The command output contract remains conservative:

```text
candidate_creation_allowed=false
evidence_created=false
artifact_downloads=false
product_writes=false
registry_config_mutated=false
```

## Local SQLite Evidence

Temporary SQLite validation with `tests/fixtures/docm_summary_2026_05_29.html`:

```text
exit_code=0
code=DOCM
external_id=DOCM:2026/4101
publication_date=2026-05-29
file_type=raw_api_response
media_type=text/html
size_bytes=1156
sha_len=64
same_hash=1
integrity_checks=1
```

## Validation

```text
python -m pytest tests/test_cli.py::test_ingest_monitor_date_records_docm_html_snapshot_file -q
1 passed

python -m pytest tests/test_html_monitor.py::test_parse_docm_fixture_emits_metadata_only_records -q
1 passed

python -m pytest tests/test_cli.py tests/test_html_monitor.py -q
226 passed

python -m pytest -q
819 passed, 2 warnings

git diff --check
passed
```

Ruff was checked but not used as a GO gate because the current repository has unrelated
pre-existing formatting/lint drift in files outside this task and in historical areas of
`cli.py`. This task did not remediate that drift.

## Result

DOCM future monitor materializations now have an integrity artifact row for the official summary
HTML snapshot. This improves downstream evidence packet readiness without downloading document
artifacts and without widening candidate, evidence-grade, downstream, or runtime write surfaces.

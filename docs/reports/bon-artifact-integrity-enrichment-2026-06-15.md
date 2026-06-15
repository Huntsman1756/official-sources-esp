# BON Artifact Integrity Enrichment

Task: `TASK-OFFICIAL-SOURCES-BON-ARTIFACT-INTEGRITY-ENRICHMENT-001`

Date: 2026-06-15

## Scope

Add BON artifact integrity support to the existing metadata materialization path.

The task stays inside upstream parser/storage coverage:

- source: `BON` only;
- command: `ingest-monitor-date`;
- artifact kind: monitor summary HTML snapshot stored as `raw_api_response`;
- no candidate creation;
- no evidence-grade promotion;
- no downstream EduBecas writes;
- no VPS SQLite mutation;
- no runtime, systemd, timer, cap, or Hermes changes.

## Implementation

The existing monitor snapshot persistence path now allows `BON` alongside `DOCM` and `BOPA`.

When `ingest-monitor-date --source BON` materializes monitor records, it persists the fetched
official summary HTML payload through `OfficialSourcesRepository.upsert_document_file`:

```text
file_type=raw_api_response
media_type=text/html
official_url=<BON issue summary URL>
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

Temporary SQLite validation with `tests/fixtures/bon_index_may_2026.html` and
`tests/fixtures/bon_summary_2026_104.html`:

```text
exit_code=0
code=BON
external_id=BON:2026.104.22
publication_date=2026-05-29
file_type=raw_api_response
media_type=text/html
official_url=https://bon.navarra.es/es/boletin/-/sumario/2026/104
source_snapshot_hash=<raw HTML sha256>
integrity_checks=1
changed=0
change_reason=new_file
```

## Validation

```text
python -m pytest tests/test_cli.py -k "bon_html_snapshot or bopa_html_snapshot or docm_html_snapshot" -q
3 passed, 113 deselected

python -m pytest tests/test_cli.py -q
116 passed

python -m pytest -q
824 passed, 2 warnings

git diff --check
passed
```

## Result

BON future monitor materializations now have an integrity artifact row for the official summary HTML
snapshot. This removes the current downstream evidence-preview blocker for BON after a separate
live snapshot backfill, without downloading document artifacts and without widening candidate,
evidence-grade, downstream, runtime, systemd, timer, cap, or Hermes write surfaces.

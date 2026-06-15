# BOPA Artifact Integrity Enrichment

Task: `TASK-OFFICIAL-SOURCES-BOPA-ARTIFACT-INTEGRITY-ENRICHMENT-001`

Date: 2026-06-15

## Scope

Add BOPA artifact integrity support to the existing metadata materialization path.

The task stays inside upstream parser/storage coverage:

- source: `BOPA` only;
- command: `ingest-monitor-date`;
- artifact kind: monitor summary HTML snapshot stored as `raw_api_response`;
- no candidate creation;
- no evidence-grade promotion;
- no downstream EduBecas writes;
- no VPS SQLite mutation;
- no runtime, systemd, timer, cap, or Hermes changes.

## Implementation

The existing monitor snapshot persistence path now allows `BOPA` alongside `DOCM`.

When `ingest-monitor-date --source BOPA` materializes monitor records, it persists the fetched
official summary HTML payload through `OfficialSourcesRepository.upsert_document_file`:

```text
file_type=raw_api_response
media_type=text/html
official_url=<BOPA date-scoped summary URL>
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

Temporary SQLite validation with `tests/fixtures/bopa_summary_2026_05_29.html`:

```text
exit_code=0
code=BOPA
external_id=BOPA:2026-04395
publication_date=2026-05-29
file_type=raw_api_response
media_type=text/html
official_url=https://miprincipado.asturias.es/bopa-sumario?p_r_p_summaryDate=29%2F05%2F2026&p_r_p_summaryIsSearch=false
source_snapshot_hash=<raw HTML sha256>
integrity_checks=1
changed=0
change_reason=new_file
```

## Validation

```text
python -m pytest tests/test_cli.py -k "bopa_html_snapshot or docm_html_snapshot" -q
2 passed, 112 deselected

python -m pytest tests/test_cli.py -q
114 passed

python -m pytest -q
822 passed, 2 warnings
```

## Result

BOPA future monitor materializations now have an integrity artifact row for the official summary
HTML snapshot. This removes the current downstream evidence-preview blocker for BOPA without
downloading document artifacts and without widening candidate, evidence-grade, downstream, runtime,
systemd, timer, cap, or Hermes write surfaces.

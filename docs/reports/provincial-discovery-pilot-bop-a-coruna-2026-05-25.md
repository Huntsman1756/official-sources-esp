# Provincial discovery pilot - BOP_A_CORUNA - 2026-05-25

Task: `TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001`

## Scope

This task adds one provincial metadata-only discovery pilot for `BOP_A_CORUNA`.

It does not create source candidates, evidence-grade records, PDFs, artifacts, backfills,
downstream writes, broad monitor runs, VPS operations, production DB operations, publication, or LLM
classification.

## Pilot Source

Selected source:

```text
BOP_A_CORUNA
```

Reason for selection:

- official landing URL is clear;
- date-scoped bulletin summary page is available;
- listing is HTML and parseable without mandatory JavaScript;
- each announcement exposes a web/HTML version URL;
- metadata can be discovered without downloading PDFs.

Official access method added to `config/sources.yaml`:

```text
type: html
url: https://bop.dacoruna.gal/bopportal/cambioBoletin.do?fechaInput={date_ddmmyyyy}
status: validated
```

`BOP_A_CORUNA` was promoted from provincial `inventory_only` to `monitor_validated`. The remaining
42 provincial sources stay inventory-only.

## CLI Command

Preview command:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli html monitor --source BOP_A_CORUNA --date 2026-05-25 --limit 1
```

Write command, only when explicitly approved:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli html monitor --source BOP_A_CORUNA --date 2026-05-25 --limit 10 --write
```

Output path when `--write` is explicitly used:

```text
data/html_monitor/BOP_A_CORUNA/<YYYY-MM-DD>/html_discovery.jsonl
```

## Metadata Fields

HTML discovery records emit:

```text
source_code
page_url
page_format
entry_id
document_id
title
published_at
official_url
summary
raw_page_hash
entry_hash
discovered_at
monitor_run_id
classification_status
evidence_status
candidate_status
warnings
```

Safety fields remain:

```text
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

## Hashing Strategy

`raw_page_hash` is SHA-256 of the raw HTML page payload.

`entry_hash` is deterministic:

```text
SHA256(source_code + published_at + official_url)
```

If `official_url` is missing, the fallback is:

```text
SHA256(source_code + document_id + title)
```

and the record receives `entry_hash_fallback_missing_official_url`.

## Live Preview Result

Live preview was run without `--write`:

```text
command_started=html monitor source_code=BOP_A_CORUNA date=2026-05-25 mode=preview records=1 discovery_metadata_only=true
```

First record:

```text
document_id=2026/3193
official_url=https://bop.dacoruna.gal/bopportal/2026_0000003193.html
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

No `data/html_monitor/` output directory was created by the preview.

## MCP Coverage

`list_monitorable_sources` can now expose `BOP_A_CORUNA` as HTML-monitorable because the registry
declares a validated HTML access method and `monitor_support=available`.

`list_latest_discovery_entries` still reads existing RSS/API JSONL only. Exposing existing
HTML monitor JSONL through MCP remains a separate possible task:

```text
TASK-MCP-HTML-DISCOVERY-OUTPUT-001
```

## Safety Confirmation

Confirmed:

- no `source_candidates` were created;
- no evidence-grade records were created;
- no PDFs were downloaded;
- no artifacts were created;
- no downstream repositories were touched;
- no backfills were run;
- no broad/all-source monitor runs were run;
- no JSONL writes were run in the live preview;
- no VPS operations were run;
- no production DB operations were run;
- no LLM classification was added.

## Next Recommended Task

Recommended next task:

```text
TASK-MCP-HTML-DISCOVERY-OUTPUT-001
```

Only if the MCP needs to read existing HTML discovery JSONL. It should remain read-only and must not
fetch live HTML or write files.

Otherwise, choose at most 1-2 additional provincial sources for a second pilot only after
source-specific access-path verification.

# BOPV API discovery adapter - 2026-05-24

Task: `TASK-SOURCE-BOPV-API-001`

## Scope

This task adds metadata-only REST/API discovery for BOPV. It is a monitoring/control-plane
capability, not evidence-grade ingestion.

It does not create candidates, evidence-grade records, PDFs, artifacts, backfills, downstream
writes, VPS operations, production DB operations, publication, or LLM classification.

## Endpoint

BOPV now has a validated API access method in `config/sources.yaml`:

```text
https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}
```

Runtime requests are bounded to one source and one month derived from `--date`:

```text
https://api.euskadi.eus/bopv/administrative-acts/2026/5?currentPage=1&itemsOfPage=1&lang=SPANISH
```

The public documentation surface is Open Data Euskadi's BOPV REST API page:

```text
https://opendata.euskadi.eus/api-bopv/?api=bopv
```

Access method status: `validated`.

## Adapter

New module:

```text
src/official_sources/api_monitor.py
```

The adapter emits metadata-only discovery records with:

```text
source_code
api_url
api_endpoint
title
published_at
official_url
document_id
api_id
summary
raw_response_hash
entry_hash
discovered_at
monitor_run_id
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

The adapter intentionally excludes the API `text` body from discovery output.

## CLI

New command:

```bash
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit N
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit N --write
```

Behavior:

- one source at a time;
- broad/all-source runs are refused;
- non-API sources are refused;
- default mode is preview;
- writes require explicit `--write`;
- output is labelled discovery metadata only.

## Output

Explicit writes go to:

```text
data/api_monitor/BOPV/<YYYY-MM-DD>/api_discovery.jsonl
```

The write path is deterministic and replayable for a given source/date/output root.

## Hashing

`raw_response_hash` is SHA256 of the raw API response payload bytes.

`entry_hash` is deterministic:

```text
SHA256(source_code + published_at + official_url)
```

If `official_url` is unavailable, the fallback is:

```text
SHA256(source_code + api_id)
```

Fallback use is recorded in the record warnings.

## Live Preview

Live bounded preview was run without `--write`:

```bash
PYTHONPATH=src python -c "from official_sources.cli import main; main()" api monitor --source BOPV --date 2026-05-24 --limit 1
```

Result:

```text
records=1
api_id=2026/05/1813
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

The local command used `PYTHONPATH=src` to force the current branch source tree; the installed
console entry point may point at an older local package until reinstalled.

## Guardrail Confirmation

This task did not create:

- `source_candidates`
- evidence-grade records
- PDFs
- artifact files
- downstream product writes
- backfills
- broad historical imports
- broad/all-source monitor runs
- VPS operations
- production DB operations
- LLM classification

RSS monitor behavior was not changed.

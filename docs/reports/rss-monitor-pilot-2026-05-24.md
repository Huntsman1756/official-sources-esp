# RSS monitor pilot - 2026-05-24

Task: `TASK-SOURCE-RSS-MONITOR-001`

Base registry commit:

```text
fc5544c docs/config: add canonical executable source registry
```

## Why RSS/Atom Is Discovery-Only

RSS/Atom feeds are notification and discovery surfaces. They can reveal that a bulletin item exists,
but they do not replace the evidence-grade flow that uses scoped official metadata, review records,
citations, integrity metadata, and explicit artifact handling.

RSS/Atom records emitted by this task are therefore labeled:

```text
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

They must not be promoted to source candidates, evidence-grade records, artifacts, or downstream
product output without a separate explicit task.

## Pilot Source

Pilot source:

```text
BOCYL
```

The BOCYL registry entry now includes a validated RSS access method:

```text
https://bocyl.jcyl.es/rss.do
```

The RSS index page observed during the task was:

```text
https://bocyl.jcyl.es/indiceRss.do
```

It states that BOCYL offers RSS 2.0 and Atom 1.0 feeds. This task validates and uses the complete
BOCYL RSS 2.0 feed only.

## BOE Control

BOE was not used as a control in this task. The parser is covered by small RSS 2.0 and Atom 1.0
fixtures, and BOCYL is sufficient for the first live source contract.

## Metadata Fields

Each discovery record includes:

- `source_code`
- `feed_url`
- `feed_format`
- `entry_id`
- `title`
- `published_at`
- `updated_at`
- `official_url`
- `summary`
- `raw_feed_hash`
- `entry_hash`
- `discovered_at`
- `monitor_run_id`
- `classification_status`
- `evidence_status`
- `candidate_status`
- `warnings`

## Output Path

Default output root:

```text
data/rss_monitor
```

JSONL output path:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

Writes require explicit `--write`. Without `--write`, the command prints a preview and does not
create JSONL files.

## CLI Commands

Preview:

```bash
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit N
```

Write:

```bash
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit N --write
```

The command:

- accepts one source at a time;
- rejects `ALL`, `*`, and comma-separated source lists;
- rejects sources without a validated RSS/Atom access method;
- reads `config/sources.yaml`;
- does not open SQLite;
- does not call source candidate, evidence, artifact, downstream, VPS, or production DB paths.

## Hashing Strategy

`raw_feed_hash` is:

```text
SHA256(raw feed payload bytes)
```

`entry_hash` prefers:

```text
SHA256(source_code + published_at + official_url)
```

If `official_url` is missing, it falls back to:

```text
SHA256(source_code + entry_id + title)
```

Fallback records include:

```text
warnings=["entry_hash_fallback_missing_official_url"]
```

## What Was Not Done

This task did not:

- create `source_candidates`;
- create evidence-grade records;
- download PDFs;
- create artifact files;
- run backfills;
- run VPS operations;
- run production DB operations;
- add LLM classification;
- publish anything;
- touch downstream repositories;
- modify mature BOE/BOCYL ingestion behavior;
- implement BOPV RSS or REST/API discovery.

## Future Task

```text
TASK-SOURCE-BOPV-API-001 - BOPV REST/API discovery adapter
```

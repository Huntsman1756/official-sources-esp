# Source Coverage Run Plan

Task: `TASK-SOURCE-COVERAGE-SCHEDULE-001`

This document defines how to run source discovery monitors safely. It is a control-plane runbook,
not an automation implementation and not a scheduler deployment.

## Purpose

The source coverage platform now has:

```text
config/sources.yaml
RSS/Atom discovery: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery: BOPV
HTML discovery: BOP_A_CORUNA
MCP read-only coverage and discovery readers
MCP controlled one-source discovery preview
```

The operating rule is simple: discovery runs must remain bounded, cache-first, and metadata-only.

## Non-Goals

This plan does not:

- add cron, systemd, queue workers, GitHub Actions, or VPS jobs;
- run broad all-source monitoring;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- run backfills;
- write downstream product repositories;
- run production database operations;
- add LLM classification;
- publish or approve anything.

## Run Modes

### Preview

Preview is the default mode. It may fetch one declared source endpoint and print discovery metadata
without writing JSONL.

Allowed preview examples:

```bash
official-sources rss monitor --source BOE --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOJA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOIB --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOC_CANTABRIA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source DOE --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 1
```

Preview rules:

- one source per command;
- one date per command;
- small `--limit`;
- no `--write`;
- no downstream side effects;
- no candidate or evidence-grade creation.

### Explicit Write

Write mode is allowed only when the task explicitly authorizes metadata-only discovery output.

Allowed write examples:

```bash
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 10 --write
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 10 --write
```

Write output paths:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

Write rules:

- use one source per command;
- use one date per command;
- record the command and output path in a report;
- inspect output row count after writing;
- do not treat output as candidates;
- do not treat output as evidence;
- do not trigger downstream imports.

## Refused Runs

The CLI must continue refusing broad source selectors:

```bash
official-sources rss monitor --source ALL --date YYYY-MM-DD --limit 1
official-sources rss monitor --source "*" --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOE,BOJA --date YYYY-MM-DD --limit 1

official-sources api monitor --source ALL --date YYYY-MM-DD --limit 1
official-sources api monitor --source "*" --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV,BOE --date YYYY-MM-DD --limit 1

official-sources html monitor --source ALL --date YYYY-MM-DD --limit 1
official-sources html monitor --source "*" --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_A_CORUNA,BOP_ZARAGOZA --date YYYY-MM-DD --limit 1
```

The API monitor must also refuse non-API sources.
The HTML monitor must also refuse sources without a validated HTML access method.

## Pre-Run Checklist

Before any discovery run:

1. Confirm the working tree is clean or unrelated dirty files are outside the task.
2. Confirm the intended source is registered:

   ```bash
   official-sources sources status --source <SOURCE_CODE>
   ```

3. Confirm the source has an appropriate access method:

   - RSS/Atom monitor requires `rss` or `atom`.
   - API monitor requires `api`.
   - HTML monitor requires `html`.

4. Confirm safety flags remain false unless a separate explicit task changed them:

   ```text
   candidate_creation_allowed=False
   evidence_grade_allowed=False
   ```

5. Decide mode:

   - preview: default;
   - write: only if the task explicitly says to write metadata-only JSONL.

6. Set a small limit for first execution:

   ```text
   --limit 1
   ```

## Standard Run Sequence

For a safe preview:

```bash
official-sources sources status --source <SOURCE_CODE>
official-sources rss monitor --source <SOURCE_CODE> --date YYYY-MM-DD --limit 1
```

or:

```bash
official-sources sources status --source <SOURCE_CODE>
official-sources api monitor --source <SOURCE_CODE> --date YYYY-MM-DD --limit 1
```

or:

```bash
official-sources sources status --source <SOURCE_CODE>
official-sources html monitor --source <SOURCE_CODE> --date YYYY-MM-DD --limit 1
```

For an explicitly approved write:

```bash
official-sources sources status --source <SOURCE_CODE>
official-sources rss monitor --source <SOURCE_CODE> --date YYYY-MM-DD --limit 10 --write
```

or:

```bash
official-sources sources status --source <SOURCE_CODE>
official-sources api monitor --source <SOURCE_CODE> --date YYYY-MM-DD --limit 10 --write
```

Then inspect:

```text
output_path=<reported JSONL path>
records=<reported count>
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

## Post-Run Checklist

After any run:

1. Confirm no unexpected files were created.
2. If `--write` was not used, confirm no JSONL output was written.
3. If `--write` was used, confirm the output path is under the expected monitor directory.
4. Confirm every inspected record remains:

   ```text
   candidate_status=not_candidate
   evidence_status=not_evidence
   classification_status=unclassified
   ```

5. Do not run downstream commands.
6. Do not run candidate commands.
7. Do not run evidence review commands.
8. Do not download PDFs or artifacts.

## Run Report Template

Every non-trivial discovery execution should add or update a report under `docs/reports/`.

Recommended filename:

```text
docs/reports/source-discovery-run-<source_code>-<YYYY-MM-DD>.md
```

Template:

````markdown
# Source discovery run - <SOURCE_CODE> - <YYYY-MM-DD>

Task: `<TASK_ID>`

## Scope

- source: `<SOURCE_CODE>`
- monitor type: `rss` | `atom` | `api`
- mode: `preview` | `write`
- date: `<YYYY-MM-DD>`
- limit: `<N>`

## Commands

```bash
official-sources sources status --source <SOURCE_CODE>
official-sources <rss|api> monitor --source <SOURCE_CODE> --date <YYYY-MM-DD> --limit <N>
```

## Results

```text
records=<N>
output_path=<path or none>
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

## Guardrails

Confirm:

- no `source_candidates` were created;
- no evidence-grade records were created;
- no PDFs or artifacts were downloaded;
- no downstream repositories were touched;
- no backfills were run;
- no broad/all-source run was used;
- no VPS or production DB operations were run.
````

## MCP Readback

MCP readback is optional and read-only. It may be used after a JSONL write to confirm existing output
can be read:

```text
list_latest_discovery_entries
```

MCP must not:

- fetch live RSS/API/HTML data from cache readback tools;
- write JSONL;
- create candidates;
- create evidence-grade records.

## MCP Preview

The MCP may run a controlled discovery preview through:

```text
preview_discovery
```

Allowed preview examples:

```json
{"source_code": "BOCYL", "date": "YYYY-MM-DD", "limit": 1}
{"source_code": "BOPV", "date": "YYYY-MM-DD", "limit": 1}
{"source_code": "BOP_A_CORUNA", "date": "YYYY-MM-DD", "limit": 1}
```

MCP preview rules:

- one explicit source only;
- one date only;
- default limit is 1;
- maximum limit is 10;
- no JSONL writes;
- no file creation;
- no candidates;
- no evidence-grade records;
- no PDFs or artifacts;
- no registry mutation;
- no backfills;
- no downstream writes.

The MCP preview tool may fetch one declared source endpoint to produce metadata-only records. It is
not a scheduler, not an all-source runner, and not a write path.

## Failure Handling

If a preview or write fails:

1. Stop after the single-source failure.
2. Do not retry with a broader run.
3. Record source, date, command, exit code, and error.
4. Classify the issue as one of:

   ```text
   registry_config
   source_endpoint
   parser_contract
   network_transient
   output_write
   unknown
   ```

5. Leave the source operational status unchanged unless a separate registry task updates it.

## Future Automation Gate

Do not add cron, systemd, GitHub Actions, or VPS scheduling until a separate task defines:

- schedule frequency;
- allowed source list;
- maximum per-run limit;
- write authorization;
- log/report location;
- failure alerting;
- rollback or disable procedure.

Automation must preserve the same rule: one source per monitor command.

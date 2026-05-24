# Source coverage schedule plan - 2026-05-24

Task: `TASK-SOURCE-COVERAGE-SCHEDULE-001`

## Scope

This task adds a controlled run plan for source discovery monitoring.

It is documentation/control-plane only. It does not add scheduler code, cron, systemd, GitHub
Actions, VPS jobs, new sources, monitor behavior changes, candidates, evidence-grade records,
PDFs, artifacts, downstream writes, backfills, production DB operations, publication, or LLM
classification.

## Runbook Added

Primary runbook:

```text
docs/SOURCE_COVERAGE_RUN_PLAN.md
```

The runbook defines:

- preview mode as the default;
- explicit `--write` as the only write path;
- one source per command;
- one date per command;
- small first-run limits;
- cache-first JSONL output paths;
- refused broad/all-source selectors;
- post-run checks;
- report template for discovery executions;
- future automation gates.

## Controlled Commands

Allowed preview examples:

```bash
official-sources rss monitor --source BOE --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOJA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
```

Allowed write examples only when explicitly approved:

```bash
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 10 --write
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 10 --write
```

Expected output paths:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
```

## Guardrails

The run plan requires:

- no all-source runs;
- no comma-separated source runs;
- no candidate creation;
- no evidence-grade promotion;
- no PDF/artifact download;
- no downstream writes;
- no backfills;
- no production DB operations;
- no VPS operations;
- no LLM classification.

Discovery records remain:

```text
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

## MCP Boundary

MCP remains read-only.

`list_latest_discovery_entries` may read existing JSONL output after a write, but MCP must not:

- fetch live RSS/API data;
- run monitors;
- write JSONL;
- create candidates;
- create evidence-grade records.

## Validation

Validation commands run for this task:

```bash
git diff --check
python -m ruff check src tests
python -m pytest -q
official-sources sources list
official-sources sources status --source BOCYL
official-sources sources status --source BOPV
```

Results:

```text
git diff --check: ok
python -m ruff check src tests: ok
python -m pytest -q: 488 passed, 1 warning
official-sources sources list: ok
official-sources sources status --source BOCYL: ok
official-sources sources status --source BOPV: ok
```

The pytest warning is the existing Starlette `python_multipart` pending deprecation warning.

## Next Work

Recommended next tasks:

- `TASK-SOURCE-RSS-MONITOR-003`: add 2-3 verified RSS/Atom feeds after source-specific validation.
- `TASK-SOURCE-HTML-MONITOR-PILOT-001`: pilot metadata-only HTML discovery for a source without
  RSS/API.

Candidates and evidence-grade expansion should remain out of scope until explicitly approved for a
specific source.

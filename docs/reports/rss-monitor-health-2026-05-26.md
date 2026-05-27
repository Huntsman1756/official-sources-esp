# RSS monitor health check - 2026-05-26

Task: `TASK-SOURCE-RSS-MONITOR-HEALTH-001`

## Scope

This task validates the stability of the current RSS monitor surface after `TASK-SOURCE-RSS-MONITOR-004`
was merged.

It does not add feeds, change monitor code, change parser behavior, write JSONL output, create
candidates, create evidence-grade records, download PDFs/artifacts, touch downstream repositories,
run backfills, run broad monitoring, touch VPS/prod DB, touch Hermes, or touch systemd.

Health-check source set:

```text
BOE
BOCYL
BOC_CANARIAS
DOG
BOP_LUGO
```

This set combines the current positive/control RSS sources requested for post-merge validation. It
is not a complete list of every RSS/Atom-capable source in `config/sources.yaml`.

## Commands

All previews were run one source at a time with `--limit 1` and without `--write`:

```powershell
python -m official_sources.cli rss monitor --source BOE --date 2026-05-26 --limit 1
python -m official_sources.cli rss monitor --source BOCYL --date 2026-05-26 --limit 1
python -m official_sources.cli rss monitor --source BOC_CANARIAS --date 2026-05-26 --limit 1
python -m official_sources.cli rss monitor --source DOG --date 2026-05-26 --limit 1
python -m official_sources.cli rss monitor --source BOP_LUGO --date 2026-05-26 --limit 1
```

Safety checks:

```powershell
Test-Path data\rss_monitor
git status --short --branch
python -m pytest tests/test_rss_monitor.py tests/test_source_registry.py -q
```

## Results

```text
BOE:          records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOCYL:        records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOC_CANARIAS: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
DOG:          records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOP_LUGO:     records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
```

Boundary checks:

```text
before data/rss_monitor exists: false
after data/rss_monitor exists: false
git status after previews: main...origin/main, no file changes
targeted tests: 35 passed
```

## Safety Confirmation

The preview validation used no `--write` flag.

It did not:

- create `data/rss_monitor`;
- create candidates;
- create evidence-grade records;
- download PDFs;
- write artifacts;
- write downstream data;
- run backfills;
- run broad/all-source monitoring;
- touch VPS/prod DB;
- touch Hermes;
- touch systemd.

`BOCYL` and `BOP_LUGO` records can expose PDF links inside feed metadata, but the RSS monitor did
not fetch those PDFs.

## Deferred Source Issues

Do not add another RSS batch immediately from this health check.

Known problematic/deferred sources remain deferred:

- `BORM`: official web surface declares RSS-like routes, but direct fetches previously returned a
  Radware captcha page in this environment.
- `BOP_ALMERIA`: previously rejected/deferred for the provincial HTML path because the tested
  official surface is a ZK/JavaScript app.

The next more useful task is to clean up deterministic source recommendations so already rejected or
documented-as-problematic sources are not repeatedly suggested without new evidence.

Suggested follow-up:

```text
TASK-MCP-SOURCE-RANKING-CLEANUP-001
```

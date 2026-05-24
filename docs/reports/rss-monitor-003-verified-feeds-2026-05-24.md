# RSS monitor 003 verified feeds - 2026-05-24

Task: `TASK-SOURCE-RSS-MONITOR-003`

## Scope

This task expands metadata-only RSS/Atom discovery to three additional verified official feeds.

Added sources:

| Source | Feed type | Feed URL | Access status |
| --- | --- | --- | --- |
| BOIB | rss | `https://www.caib.es/eboibfront/es/rss` | validated |
| BOC_CANTABRIA | rss | `https://www.cantabria.es/o/BOC/feed/6802081` | validated |
| DOE | rss | `https://doe.juntaex.es/rss/rss.php?seccion=6` | validated |

Existing RSS/Atom discovery sources remain:

```text
BOE
BOJA
BOCYL
```

## Verification

BOIB:

- Official BOIB landing page exposes an alternate RSS feed.
- The feed endpoint returned HTTP 200 with `application/rss+xml`.
- The RSS parser accepted the endpoint in preview mode.

BOC_CANTABRIA:

- The BOC site links to the official Cantabria RSS directory.
- The selected feed returned HTTP 200 with XML RSS content.
- This feed is category-scoped for `1 Disposiciones Generales`; it is not complete bulletin coverage.

DOE:

- The DOE RSS page lists official section feeds.
- The selected `SUMARIO COMPLETO` endpoint returned HTTP 200 with XML RSS content.
- The endpoint is valid for discovery monitoring even when the current response has no item for the preview date.

Not added:

- DOGC: tested candidate RSS URLs returned 404; no stable official RSS/Atom feed was verified.
- BON: tested candidate RSS URLs returned 404; no stable official RSS/Atom feed was verified.

## Output

The output format is unchanged:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

JSONL output is written only with explicit `--write`. This task used preview mode only.

## Safety Boundary

RSS discovery remains metadata-only:

```text
classification_status=unclassified
candidate_status=not_candidate
evidence_status=not_evidence
```

This task did not:

- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- write downstream repositories;
- run backfills;
- run broad/all-source monitoring;
- write RSS/API JSONL;
- run VPS operations;
- run production DB operations;
- add LLM classification;
- publish anything.

## Validation

Intended CLI equivalents:

```bash
official-sources rss monitor --source BOIB --date 2026-05-24 --limit 1
official-sources rss monitor --source BOC_CANTABRIA --date 2026-05-24 --limit 1
official-sources rss monitor --source DOE --date 2026-05-24 --limit 1
```

The global `official-sources` console script in this environment was stale, so the live previews were
run through the source-tree entrypoint:

```powershell
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" rss monitor --source BOIB --date 2026-05-24 --limit 1
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" rss monitor --source BOC_CANTABRIA --date 2026-05-24 --limit 1
$env:PYTHONPATH='src'; python -c "from official_sources.cli import main; raise SystemExit(main())" rss monitor --source DOE --date 2026-05-24 --limit 1
```

Preview results:

```text
BOIB: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOC_CANTABRIA: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
DOE: records=0 feed_format=rss
```

The previews were one-source-at-a-time and did not use `--write`.

Validation results:

```text
git diff --check: OK
python -m ruff check src tests: OK
python -m pytest -q: 494 passed, 1 warning
```

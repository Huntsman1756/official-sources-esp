# RSS monitor expansion - 2026-05-24

Task: `TASK-SOURCE-RSS-MONITOR-002`

## Sources Added

Two sources were added to metadata-only RSS/Atom discovery:

| source_code | feed_type | feed_url |
| --- | --- | --- |
| `BOE` | `rss` | `https://www.boe.es/rss/boe.php` |
| `BOJA` | `atom` | `https://www.juntadeandalucia.es/boja/distribucion/boja.xml` |

Existing pilot source retained:

| source_code | feed_type | feed_url |
| --- | --- | --- |
| `BOCYL` | `rss` | `https://bocyl.jcyl.es/rss.do` |

DOGC was not added in this task because no stable official RSS/Atom feed was verified. BOPV was
intentionally left out because its proper path remains REST/API discovery.

## Access Method Evidence

BOE:

- Official RSS channel index: `https://www.boe.es/rss/`
- Complete daily BOE RSS feed: `https://www.boe.es/rss/boe.php`
- Live check: HTTP 200, XML root `rss`

BOJA:

- Official Junta feed directory: `https://www.juntadeandalucia.es/informacion/fuentesweb.html`
- Complete BOJA feed: `https://www.juntadeandalucia.es/boja/distribucion/boja.xml`
- Live check: HTTP 200, XML root `{http://www.w3.org/2005/Atom}feed`

## Live Preview

Live previews were run one source at a time with `--limit 1` and without `--write`:

```bash
PYTHONPATH=src python -c "from official_sources.cli import main; main()" rss monitor --source BOE --date 2026-05-24 --limit 1
PYTHONPATH=src python -c "from official_sources.cli import main; main()" rss monitor --source BOJA --date 2026-05-24 --limit 1
```

Results:

- BOE preview returned `records=1`, `feed_format=rss`, `candidate_status=not_candidate`,
  `evidence_status=not_evidence`.
- BOJA preview returned `records=1`, `feed_format=atom`, `candidate_status=not_candidate`,
  `evidence_status=not_evidence`.

The local command used `PYTHONPATH=src` to force the current branch source tree; the installed
console entry point may point at an older local package until reinstalled.

## Output Format

JSONL output remains unchanged and requires explicit `--write`:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

Each discovery record remains metadata-only:

```text
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

## Guardrail Confirmation

This task did not create:

- `source_candidates`
- evidence-grade records
- PDFs
- artifact files
- downstream product writes
- backfills
- broad/all-source monitor runs
- VPS operations
- production DB operations
- LLM classification

The CLI still refuses broad/all-source runs. MCP discovery reads remain read-only and do not fetch
live feeds.

## Future Task

Keep BOPV separate:

```text
TASK-SOURCE-BOPV-API-001 - BOPV REST/API discovery adapter
```

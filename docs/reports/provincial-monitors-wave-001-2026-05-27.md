# Provincial Monitors Wave 001

Date: 2026-05-27

Task: `TASK-PROVINCIAL-MONITORS-WAVE-001`

## Decision

Add source-specific, metadata-only HTML discovery monitors for the first two provincial candidates
selected from the read-only batch audit:

```text
BOP_BARCELONA
BOP_MALAGA
```

Both sources are promoted from `inventory_only` to `monitor_validated` because their official
current-bulletin HTML pages can be fetched read-only and parsed into discovery metadata without
candidate creation, evidence-grade records, PDF downloads, artifact writes, or downstream writes.

## Scope

Changed:

- `config/sources.yaml`
- `src/official_sources/html_monitor.py`
- `tests/test_html_monitor.py`
- `tests/test_mcp_tools.py`
- `tests/test_provincial_readonly_audit.py`
- `tests/fixtures/bop_barcelona_latest.html`
- `tests/fixtures/bop_malaga_latest.html`
- `PROJECT_STATE.md`
- `TASK_QUEUE.md`

Not changed:

- VPS checkout
- Hermes configuration
- systemd units
- BOE timer
- integrity timer
- downstream repositories
- candidate or evidence-grade workflows
- PDF/artifact storage

## Source Notes

| Source | Official HTML page | Parser evidence | Limitation |
| --- | --- | --- | --- |
| `BOP_BARCELONA` | `https://bop.diba.cat/butlleti-del-dia` | Current page exposes card-based announcement blocks with register number, publication date, title, and official announcement URL. | Current bulletin page only; not a historical backfill interface. |
| `BOP_MALAGA` | `http://www.bopmalaga.es/` | Current page exposes article blocks with `Ver edicto` links, summary text, and publication date in the page title. | Current bulletin page only; uses a read-only User-Agent header because the site rejects a bare client request. |

## Live Preview

Ran one source at a time with `--limit 1`, preview mode only, and no `--write`:

```text
rtk python -m official_sources.cli html monitor --source BOP_BARCELONA --date 2026-05-27 --limit 1
```

Result:

```text
records=1
published_at=2026-05-27
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

```text
rtk python -m official_sources.cli html monitor --source BOP_MALAGA --date 2026-05-27 --limit 1
```

Result:

```text
records=1
published_at=2026-05-27
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

Additional parser smoke without writes:

```text
BOP_BARCELONA: 20 current-page records parsed
BOP_MALAGA: 19 current-page records parsed
```

## Registry Impact

Current counts after this wave:

```text
total sources: 65
metadata_adapter_validated: 9
monitor_validated: 11
inventory_only: 44
paused: 1
provincial inventory-only sources: 37
```

Provincial HTML discovery sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_BARCELONA
BOP_MALAGA
```

## Safety

The monitors remain metadata-only:

```text
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
candidate_creation_allowed=false
evidence_grade_allowed=false
```

The task did not run broad scraping or backfills, did not download PDFs/artifacts, did not write
discovery JSONL during validation, and did not touch operational infrastructure.

## Next

Review and merge this small wave before starting another provincial monitor PR. The next likely
wave is at most 1-2 sources from the audit evidence, not a bulk rollout.

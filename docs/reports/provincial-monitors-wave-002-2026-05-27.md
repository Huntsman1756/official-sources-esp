# Provincial Monitors Wave 002

Date: 2026-05-27

Task: `TASK-PROVINCIAL-MONITORS-WAVE-002`

## Decision

Add source-specific, metadata-only HTML discovery monitors for the next two provincial candidates
selected from the read-only batch audit:

```text
BOP_BIZKAIA
BOP_VALENCIA
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
- `tests/fixtures/bop_bizkaia_landing.html`
- `tests/fixtures/bop_bizkaia_detail.html`
- `tests/fixtures/bop_valencia_latest.html`
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
| `BOP_BIZKAIA` | `https://www.bizkaia.eus/es/bob` | The official landing page exposes a public latest-bulletin detail URL. The monitor follows that link and parses announcement rows with title, publication date from the detail URL, and official PDF URL as metadata only. | Requires two read-only requests for the source: landing page plus the linked current-bulletin detail page. Not a historical backfill interface. |
| `BOP_VALENCIA` | `https://bop.dival.es/bop/drvisapi.dll` | The current page exposes `div.anuncio` blocks with title, register number, and publication date. | Announcement PDF actions are JavaScript/AJAX links, so `official_url` remains `null` and entry hashing falls back to source/date/document/title metadata. |

## Live Preview

Ran one source at a time with `--limit 1`, preview mode only, and no `--write`:

```text
rtk python -m official_sources.cli html monitor --source BOP_BIZKAIA --date 2026-05-27 --limit 1
```

Result:

```text
records=1
published_at=2026-05-27
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
warnings=["pdf_endpoint_not_downloaded"]
```

```text
rtk python -m official_sources.cli html monitor --source BOP_VALENCIA --date 2026-05-27 --limit 1
```

Result:

```text
records=1
published_at=2026-05-27
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
warnings=["entry_hash_fallback_missing_official_url"]
```

Additional parser smoke without writes:

```text
BOP_BIZKAIA: 34 current-page records parsed
BOP_VALENCIA: 25 current-page records parsed
```

## Registry Impact

Current counts after this wave:

```text
total sources: 65
metadata_adapter_validated: 9
monitor_validated: 13
inventory_only: 42
paused: 1
provincial inventory-only sources: 35
```

Provincial HTML discovery sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_BARCELONA
BOP_BIZKAIA
BOP_MALAGA
BOP_VALENCIA
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
candidate from the prior audit is `BOP_SEVILLA`, but it should still be validated through a separate
source-specific task.

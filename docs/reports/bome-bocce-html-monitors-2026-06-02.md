# BOME and BOCCE HTML Monitors - 2026-06-02

Task: `TASK-BOME-BOCCE-HTML-MONITORS-2026-06-02`

## Verdict

`BOME` and `BOCCE` are promoted from `inventory_only` to `monitor_validated` metadata-only HTML
discovery sources.

Current registry baseline:

```text
registered sources: 67
metadata_adapter_validated: 10
monitor_validated: 56
inventory_only: 1
remaining inventory_only source: DOUE
candidate_creation_allowed=false: 67
evidence_grade_allowed=false: 67
```

## Scope

Implemented:

- `BOME`: landing page fetch, matching issue-page resolution for one requested date, and article
  metadata extraction from the issue HTML.
- `BOCCE`: official listing-page fetch and issue-level metadata extraction for one requested date.

Not implemented:

- PDF/artifact downloads.
- Candidate creation.
- Evidence-grade records.
- Broad backfill.
- Downstream writes.
- VPS, Hermes, systemd, or timer changes.

## Live Preview Evidence

```powershell
rtk python -m official_sources.cli html monitor --source BOME --date 2026-05-29 --limit 1
```

Result:

```text
command_started=html monitor source_code=BOME date=2026-05-29 mode=preview records=1 discovery_metadata_only=true
candidate_status=not_candidate
evidence_status=not_evidence
official_url=https://bomemelilla.es/bome/BOME-B-2026-6383/articulo/606
document_id=BOME-A-2026-606
```

```powershell
rtk python -m official_sources.cli html monitor --source BOCCE --date 2026-06-02 --limit 1
```

Result:

```text
command_started=html monitor source_code=BOCCE date=2026-06-02 mode=preview records=1 discovery_metadata_only=true
candidate_status=not_candidate
evidence_status=not_evidence
official_url=https://www.ceuta.es/ceuta/component/jdownloads/viewdownload/1977/23148?Itemid=
document_id=BOCCE_6622_02-06-2026
warnings=["pdf_endpoint_not_downloaded"]
```

## Validation

```powershell
rtk uv run pytest tests/test_html_monitor.py -q -k "bome or bocce"
```

Result:

```text
6 passed
```

```powershell
rtk uv run pytest tests/test_source_registry.py tests/test_html_monitor.py -q
```

Result:

```text
123 passed
```

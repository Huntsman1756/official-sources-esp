# Provincial Monitors Wave 003

Date: 2026-05-27

Task: `TASK-PROVINCIAL-MONITORS-WAVE-003`

## Summary

Wave 003 adds a single metadata-only HTML monitor:

```text
BOP_SEVILLA
```

This wave proceeds under the partial-health contract from
`TASK-BOP-ALICANTE-DEGRADED-DNS-001`:

```text
healthy monitored provincial sources before this wave: 7
degraded/manual-review sources: BOP_ALICANTE
contract: PARTIAL-GO
```

This task does not recover or modify `BOP_ALICANTE`. Alicante remains degraded/manual-review due
resolver-dependent DNS instability and is excluded from healthy-set claims.

## Implementation

`BOP_SEVILLA` now uses the official public BOP listing endpoint:

```text
https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/buscador/BOP-{date_ddmmyyyy_dash}/
```

The monitor:

```text
fetches one date-scoped HTML listing
parses li.elementoListado announcement rows
uses BOP-SE CVE values as document_id / entry_id
records HTML detail URLs as official_url
does not download PDFs
does not create candidates
does not create evidence-grade records
does not write JSONL unless --write is explicitly provided
```

Registry state:

```text
BOP_SEVILLA: inventory_only -> monitor_validated
monitor_support: available
candidate_creation_allowed: false
evidence_grade_allowed: false
```

## Live Smoke

Command:

```powershell
rtk python -m official_sources.cli html monitor --source BOP_SEVILLA --date 2026-05-27 --limit 1
```

Result:

```text
command_started=html monitor source_code=BOP_SEVILLA date=2026-05-27 mode=preview records=1 discovery_metadata_only=true
document_id=BOP-SE-2026-100001
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
official_url=https://bopsevilla.dipusevilla.es/publica/buscador-anuncios/anuncio/Bases-de-la-convocatoria-de-pruebas-selectivas-para-la-creacion-de-una-bolsa-de-empleo-extraordinaria-en-la-categoria-de-Tecnico-Superior-en-Ciencias-Ambientales/
```

Parser extraction check:

```text
BOP_SEVILLA live records parsed for 2026-05-27: 33
first document_id: BOP-SE-2026-100001
last document_id: BOP-SE-2026-100033
```

## Safety

No operational writes or infrastructure changes:

```text
no VPS checkout changes
no Hermes changes
no systemd changes
no timer changes
no BOE timer changes
no integrity timer changes
no data/html_monitor output
no data/rss_monitor output
no PDF/artifact downloads
no candidate creation
no evidence-grade output
no downstream writes
```

## Validation

Focused validation:

```text
rtk python -m pytest tests/test_html_monitor.py tests/test_mcp_tools.py -q
73 passed, 1 warning
```

Full validation:

```text
rtk python -m pytest -q
559 passed, 1 warning

rtk python -m ruff check src tests
passed

rtk git diff --check
passed

data/html_monitor: absent
data/rss_monitor: absent
```

# BDNS Adapter Hardening

Date: 2026-05-21

## Summary

TASK-BDNS-002B hardened the local BDNS adapter before any VPS ingestion.

Scope stayed limited to BDNS `convocatorias` metadata:

```text
local only
metadata only
convocatorias only
no concessions
no candidates
no downstream writes
no PDF or attachment downloads
no broad live ingestion
```

## Parser Hardening

The list parser now accepts these response shapes and identifier variants:

```text
content
items
numeroConvocatoria
codigoBDNS
codigoBdns
codigo
id
```

Date fallback coverage includes:

```text
fechaPublicacion
fechaRecepcion
fechaRegistro
```

Detail budget fallback coverage includes:

```text
presupuestoTotal
presupuesto
importeTotal
importe
```

Optional absent fields such as `organo`, department levels, `tipoConvocatoria`, application URLs,
beneficiary lists, instruments, sectors, and regions remain nullable instead of forcing failures.

## Pagination Safety

Search remains bounded by the existing hard limits:

```text
page_size <= 100
max_pages <= 10
```

The search ingestion result now reports:

```text
page_count
pagination_limit_reached
sample_identifiers
bdns_result
```

`pagination_limit_reached=true` means BDNS still advertised more pages when the configured local
`max_pages` limit stopped the loop. This is diagnostic only; it does not continue fetching.

## CLI Diagnostics

BDNS CLI output now includes:

```text
status
bdns_result
official_identifier
documents_fetched
documents_new
documents_updated
page_count
pagination_limit_reached
sample_identifiers
retry_count
throttle_triggered
last_http_status
source_snapshot_hash
error_message
```

Result classes:

```text
success
no_results
not_found
failed
```

`not_found` is used for detail payloads that do not contain a usable BDNS call payload. Empty search
pages are reported as `no_results`.

## Tests

Expanded tests cover:

```text
content vs items
codigoBDNS / codigoBdns / codigo / id
fechaPublicacion / fechaRecepcion / fechaRegistro
presupuestoTotal / presupuesto / importeTotal / importe
missing optional fields
empty results
missing numConv / detail not found
pagination bounded by max_pages
no concessions
no source candidates
no artifact download attempts
CLI fetched/new/updated diagnostics
CLI page count diagnostics
CLI pagination limit diagnostics
CLI not_found vs no_results vs failed-compatible status
CLI sample identifiers
```

## Files Changed

```text
src/official_sources/sources/bdns/parser.py
src/official_sources/sources/bdns/ingestion.py
src/official_sources/cli.py
tests/test_bdns_adapter.py
tests/test_cli_bdns.py
docs/reports/BDNS_ADAPTER_HARDENING_2026-05-21.md
```

## Validation

Required local validation for this task:

```text
rtk git diff --check
rtk python -m pytest tests/test_bdns_adapter.py tests/test_cli_bdns.py -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

## Merge Notes

The hardening only changes BDNS adapter parsing and BDNS CLI diagnostics. It does not alter other
source adapters, candidate generation, downstream project exports, or artifact download flows.

# Source Expansion Agent Wave - 2026-05-31

Scope: parallel review for sources that can expand coverage while preserving the current safety contract.

No downstream repositories were touched. No PDFs or artifacts were downloaded. No evidence-grade records or candidates were created. MCP remains read-only over stored data; these findings are for local CLI/monitor expansion.

## Implemented in this pass

### BOR

Status: implemented as a metadata-only XML API monitor.

Validated URL patterns:

```text
https://ias1.larioja.org/boletin/ExportarBoletinServlet?tipo=3&mes={m}&anio={yyyy}
https://ias1.larioja.org/boletin/ExportarBoletinServlet?tipo=1&fecha={yyyy}/{mm}/{dd}&numero={N}
https://ias1.larioja.org/boletin/ExportarBoletinServlet?tipo=2&fecha={yyyy}/{mm}/{dd}&referencia={html_ref}
```

Parser scope:

- monthly calendar resolves the official issue number for one requested date
- one daily XML summary request after the issue number is known
- one record per nested `anuncio`
- title from `titulo`
- document id and official URL from the `contenido tipo="html"` reference
- issue number and hierarchy summary from the XML section/body attributes
- `warnings=["pdf_endpoint_not_downloaded"]` when a PDF reference is present

### BOP_PONTEVEDRA

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://boppo.depo.gal/detalle/-/boppo/{yyyy}/{mm}/{dd}
```

Parser scope:

- publication date from the BOPPO detail page header
- one record per `ul.listadoSumario > li`
- issuer from `span.pub`
- title and official HTML URL from `p.sumario a`
- document id from the trailing numeric BOPPO detail URL segment
- `warnings=["pdf_endpoint_not_downloaded"]`

## Local validation evidence

```text
pytest -q tests/test_api_monitor.py tests/test_html_monitor.py tests/test_source_registry.py tests/test_provincial_readonly_audit.py
passed

python -m official_sources.cli api monitor --source BOR --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

python -m official_sources.cli html monitor --source BOP_PONTEVEDRA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence
```

VPS smoke after copying runtime files to `/opt/official-sources/app`:

```text
official-sources sources status --source BOR
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources api monitor --source BOR --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

official-sources sources status --source BOP_PONTEVEDRA
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources html monitor --source BOP_PONTEVEDRA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence
```

## Next ranked autonomous sources

### 1. DOCM - Diario Oficial de Castilla-La Mancha

Endpoint candidates:

```text
https://docm.jccm.es/docm/
https://docm.jccm.es/docm/cambiarBoletin.do?fecha={yyyymmdd}
```

Expected parser shape:

- date-scoped HTML summary page
- section heading and title text
- `[NID yyyy/nnnn]`
- detail URL as `official_url`
- no `descargarArchivo` PDF downloads

### 2. BON - Boletin Oficial de Navarra

Endpoint candidates:

```text
https://bon.navarra.es/es/inicio
https://bon.navarra.es/es/boletin/-/sumario/{yyyy}/{numero}
https://bon.navarra.es/es/anuncio/-/texto/{yyyy}/{numero}/{ordinal}
```

Expected parser shape:

- month calendar JSON maps date to bulletin number
- summary HTML provides announcement links
- `entry_id=BON:{year}:{numero}:{ordinal}`
- announcement HTML URL as `official_url`

## Next ranked provincial sources

### 1. BOP_AVILA

Endpoint candidate:

```text
https://www.diputacionavila.es/boletin-oficial/{yyyy}/{dd-mm-yyyy}.html
```

Fast path: static HTML date pages and PDF links visible in server-rendered content. Metadata-only parser should derive document ids from PDF basenames and mark `pdf_endpoint_not_downloaded`.

### 2. BOP_CORDOBA

Endpoint candidates:

```text
https://bop.dipucordoba.es/
https://bop.dipucordoba.es/dia/{dd-mm-yyyy}
```

Fast path: server-rendered current issue and announcement rows. Fixture will be noisier because of Next.js payloads, but no browser execution appears required.

## Deferred

- BOP_ZARAGOZA: previous priority is stale; current evidence remains unknown/high friction.
- BORME: defer for this project unless scoped to a metadata-only spike. External parsers are not a direct fit for the current licensing and artifact-boundary constraints.
- BOP_SORIA: promising HTML route exists, but sampled RSS was effectively empty; validate date-page HTML first.

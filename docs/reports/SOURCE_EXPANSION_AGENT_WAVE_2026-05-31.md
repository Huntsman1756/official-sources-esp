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

### BOP_AVILA

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://www.diputacionavila.es/boletin-oficial/{yyyy}/{dd_mm_yyyy}.html
```

Parser scope:

- publication date from the official page title/header
- one record per announcement PDF link in the date page
- document id from the PDF basename
- PDF URL stored only as metadata `official_url`
- `warnings=["pdf_endpoint_not_downloaded"]`

### BOP_CORDOBA

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://bop.dipucordoba.es/dia/{dd_mm_yyyy}
```

Parser scope:

- publication date from the date-scoped URL
- one record per server-returned Next.js/RSC `announcement` payload item
- title from the announcement text payload
- issuer from the nearest preceding `emisor` payload item
- PDF viewer URL stored only as metadata `official_url`
- `warnings=["pdf_endpoint_not_downloaded"]`

### BOP_GRANADA

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://bop.dipgra.es/publica/consulta-de-bops/buscador/BOP-{dd_mm_yyyy}/
```

Parser scope:

- date-scoped public BOP page
- one record per `elementoListado` announcement
- title and public announcement detail URL from `Ir al detalle`
- document id from the visible `BOP-GRA-*` code
- publication date and issuer from visible metadata
- public announcement detail URL stored as metadata `official_url`

### BOP_SORIA

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://bop.dipsoria.es/index.php/mod.boloficial/mem.listadodia/fecha.{dd_mm_yyyy}
```

Parser scope:

- date-scoped bulletin page exposes the official public detail URL
- monitor follows only that detail URL for the requested date
- publication date from the detail header/body
- one record per summary item with a document download link
- document id from the official download URL numeric segment
- hierarchy stored as `summary`
- download URL stored only as metadata `official_url`
- `warnings=["pdf_endpoint_not_downloaded"]`

### DOCM

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://docm.jccm.es/docm/cambiarBoletin.do?fecha={yyyymmdd}
```

Parser scope:

- publication date and issue number from the DOCM summary header
- one record per `disp_*` summary block
- title and NID from `p.sumario`
- official URL from the HTML document route `verArchivoHtml.do`
- category and organism in `summary`
- visible PDF links ignored except for `pdf_endpoint_not_downloaded`

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

python -m official_sources.cli html monitor --source BOP_AVILA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

python -m official_sources.cli html monitor --source BOP_CORDOBA --date 2026-05-28 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

python -m official_sources.cli html monitor --source BOP_GRANADA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

python -m official_sources.cli html monitor --source BOP_SORIA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

python -m official_sources.cli html monitor --source DOCM --date 2026-05-29 --limit 1
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

official-sources sources status --source BOP_AVILA
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources html monitor --source BOP_AVILA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

official-sources sources status --source BOP_CORDOBA
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources html monitor --source BOP_CORDOBA --date 2026-05-28 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

official-sources sources status --source BOP_GRANADA
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources html monitor --source BOP_GRANADA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

official-sources sources status --source BOP_SORIA
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources html monitor --source BOP_SORIA --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence

official-sources sources status --source DOCM
operational_status=monitor_validated
monitor_support=available
candidate_creation_allowed=False
evidence_grade_allowed=False

official-sources html monitor --source DOCM --date 2026-05-29 --limit 1
records=1
candidate_status=not_candidate
evidence_status=not_evidence
```

## Implemented in follow-up batch

### BON

Status: implemented as a metadata-only HTML monitor.

Validated URL patterns:

```text
https://bon.navarra.es/es/indice-boletines
https://bon.navarra.es/es/boletin/-/sumario/{yyyy}/{numero}
https://bon.navarra.es/es/anuncio/-/texto/{yyyy}/{numero}/{ordinal}
```

Parser scope:

- monthly index resolves requested date to official issue number
- issue summary HTML provides one record per announcement link
- document id is `{year}.{issue_number}.{ordinal}`
- summary preserves the visible BON section context
- announcement HTML URL is stored as metadata `official_url`

### BOP_HUELVA

Status: implemented as a metadata-only API monitor.

Validated URL pattern:

```text
https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php
```

Parser scope:

- monitor posts `tipo=2&fecha=YYYY-MM-DD` to the official BOP AJAX endpoint
- one record per `Anuncios` item
- document id from `num_expe`, API id from `id_anuncio`
- issue number from `Indice.num_bop`
- detail URL is stored as metadata `official_url`
- `warnings=["pdf_endpoint_not_downloaded"]` when the response exposes a PDF document reference

### BOP_PALENCIA

Status: implemented as a metadata-only HTML monitor with latest-date verification.

Validated URL pattern:

```text
https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia
```

Parser scope:

- official date filter did not return stable SSR result rows in validation
- monitor uses the latest listing and extracts the publication date from the bulletin PDF basename
- records are emitted only when the latest listing date matches the requested date
- record granularity is bulletin-level because the listing exposes bulletin/PDF entries, not granular announcements
- `warnings=["pdf_endpoint_not_downloaded"]`

### BOPA

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://miprincipado.asturias.es/bopa-sumario?p_r_p_summaryDate={dd/mm/yyyy}&p_r_p_summaryIsSearch=false
```

Parser scope:

- date-scoped official BOPA summary page
- one record per disposition `dl`
- document id from the visible `[Cod. yyyy-nnnnn]`
- official text page URL is stored as metadata `official_url`
- visible PDF links are not downloaded and add `warnings=["pdf_endpoint_not_downloaded"]`

### BOP_JAEN

Status: implemented as a metadata-only HTML monitor.

Validated URL pattern:

```text
https://bop.dipujaen.es/bop/{dd-mm-yyyy}
```

Parser scope:

- date-scoped official BOP page
- one record per `article` in the summary
- document id from `numeroEdicto` and `ejercicioBop`
- official `descargarws.dip` URL is stored as metadata only
- `warnings=["pdf_endpoint_not_downloaded"]`

### BOP_LLEIDA

Status: implemented as a metadata-only HTML monitor with latest-date verification.

Validated URL pattern:

```text
https://ebop.diputaciolleida.cat/bop/
```

Parser scope:

- latest official bulletin page
- publication date from the `Bop numero` header
- records are emitted only when latest date matches the requested date
- one record per `li.edicte`
- official PDF URL is stored as metadata only with `warnings=["pdf_endpoint_not_downloaded"]`

### BOP_ZAMORA

Status: implemented as a metadata-only two-step HTML monitor.

Validated URL patterns:

```text
https://www.diputaciondezamora.es/opencms/servicios/BOP/bop/index.html
https://www.diputaciondezamora.es/opencms/servicios/BOP/indice-bop/{uuid}/
```

Parser scope:

- listing page resolves the requested-date bulletin detail URL
- detail page emits one record per `div#anuncio`
- document id from `Nº de referencia`
- section/procedencia/organismo are preserved in `summary`
- official PDF URL is stored as metadata only with `warnings=["pdf_endpoint_not_downloaded"]`

## Follow-up batch: Burgos, Leon, Segovia, Toledo

Validated locally on 2026-05-31 as metadata-only monitors:

- `BOP_BURGOS`: date-scoped archive page plus bulletin detail page; emits announcement metadata and stores PDF endpoints as official URLs only.
- `BOP_LEON`: date-scoped bulletin page; emits bulletin-level metadata only because no stable granular announcement HTML endpoint was confirmed.
- `BOP_SEGOVIA`: official landing-page bulletin cards with requested-date verification; emits bulletin-level metadata only.
- `BOP_TOLEDO`: date-scoped summary page; emits announcement metadata and stores DocGet PDF endpoints as official URLs only.

Local live preview evidence for `2026-05-29`: all four returned `records=1`,
`candidate_status=not_candidate`, and `evidence_status=not_evidence`.

## Follow-up batch: Araba/Alava, Gipuzkoa, Caceres

Validated locally on 2026-05-31 as metadata-only monitors:

- `BOP_ARABA_ALAVA`: official date-scoped BOTHA page using `FechaBotha={dd/mm/yyyy}`; emits announcement metadata and official XML/detail URLs.
- `BOP_GIPUZKOA`: official date-scoped BOG summary page under `/gao-bog/castell/bog/{yyyy}/{mm}/{dd}/`; emits announcement metadata and public detail URLs.
- `BOP_CACERES`: official JSON service flow; calendar endpoint resolves the requested date to `idBoletin`, then `anunciosAnunciantes` returns announcement metadata. PDF endpoints are recorded only as `pdf_endpoint_not_downloaded` warnings.

Local live preview evidence:

- `BOP_ARABA_ALAVA` on `2026-05-29`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`.
- `BOP_GIPUZKOA` on `2026-05-29`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`.
- `BOP_CACERES` on `2026-05-28`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`.

Deferred after live probing:

- `BOP_CADIZ`, `BOP_CIUDAD_REAL`, and `BOP_CUENCA` exposed plausible public HTML surfaces, but standard monitor execution failed local TLS certificate validation. They remain inventory-only / blocked until a validated fetch path exists without weakening TLS verification.

### BOP_SALAMANCA

Endpoint candidate:

```text
https://salamanca.diputaciondesalamanca.es/boletin-oficial-de-la-provincia
```

Risk: calendar dates were visible, but GET/POST probes against the public BOP form did not expose
stable current bulletin records or 2026 PDF links. Keep as inventory-only until a stable endpoint is
confirmed.

## Deferred

- BOP_ZARAGOZA: previous priority is stale; current evidence remains unknown/high friction.
- BORME: defer for this project unless scoped to a metadata-only spike. External parsers are not a direct fit for the current licensing and artifact-boundary constraints.

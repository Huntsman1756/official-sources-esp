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

## Follow-up batch: Guadalajara, Las Palmas, Santa Cruz de Tenerife, Teruel

Validated locally on 2026-05-31 as metadata-only monitors:

- `BOP_GUADALAJARA`: official Joomla RSS feed under `/boletin/index.php?format=feed&type=rss`; emits bulletin summary metadata only. The feed is large because it embeds full bulletin summaries.
- `BOP_LAS_PALMAS`: official date-scoped `sumario.php` page; emits bulletin-level metadata and stores the official PDF URL only as metadata.
- `BOP_SANTA_CRUZ_TENERIFE`: official date-scoped `sumario.php` page; emits bulletin-level metadata and stores the official PDF URL only as metadata.
- `BOP_TERUEL`: official current-bulletin XPages page; emits bulletin-level metadata when the current page date matches the requested date.

Local live preview evidence for `2026-05-29`: all four returned `records=1`,
`candidate_status=not_candidate`, and `evidence_status=not_evidence`.

Deferred after VPS validation:

- `BOP_SALAMANCA`: date-scoped HTML was found and parsed locally, but the project VPS timed out
  fetching the official sede even with a 60 second timeout. Kept inventory-only until the VPS path
  is validated.

## Follow-up batch: Girona, Tarragona

Validated locally on 2026-05-31 as metadata-only monitors:

- `BOP_GIRONA`: official DDGI current-bulletin page at `https://www.ddgi.cat/bop/`; emits announcement metadata when the page bulletin date matches the requested date. PDF endpoints are stored only as official metadata and marked `pdf_endpoint_not_downloaded`.
- `BOP_TARRAGONA`: official date-scoped BOPT page at `https://aplicacions.dipta.cat/bopt/web/anteriores/{date}`; emits announcement-card metadata from page one only.

Local live preview evidence for `2026-05-29`:

- `BOP_GIRONA`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=202610204663`.
- `BOP_TARRAGONA`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=359557`.

Registry impact after this batch:

- `monitor_validated`: 45
- `inventory_only`: 11
- provincial `inventory_only`: 8
- normal next-source ranking: `BOP_ZARAGOZA`, `BOP_CIUDAD_REAL`, `BOP_CUENCA`, `BOP_HUESCA`, `BOP_OURENSE`, `BOP_SALAMANCA`.

## Follow-up batch: Huesca

Validated locally on 2026-06-01 as metadata-only monitor:

- `BOP_HUESCA`: official current-bulletin BOPH page at `https://bop.dphuesca.es/index.php/mod.bopanuncios/mem.ultimoboletin/idmenu.50004/seccion.portal/chk.b6a0e09090757bcdf5de25060e5c4cf5.html`; emits announcement metadata when the page bulletin date matches the requested date. PDF endpoints are stored only as official metadata and marked `pdf_endpoint_not_downloaded`.

Local live preview evidence for `2026-06-01`:

- `BOP_HUESCA`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=256954`, `issue_number=101`.

Registry impact after this batch:

- `monitor_validated`: 46
- `inventory_only`: 10
- provincial `inventory_only`: 7
- normal next-source ranking: `BOP_ZARAGOZA`, `BOP_CIUDAD_REAL`, `BOP_CUENCA`, `BOP_OURENSE`, `BOP_SALAMANCA`.

Still deferred after 2026-06-01 probes:

- `BOP_ALMERIA`: official surface remains ZK/JavaScript; plain GET does not expose deterministic bulletin records.
- `BOP_CUENCA`: official endpoint returned `403 Forbidden` / TLS fetch failure in standard monitor path.
- `BOP_OURENSE`: standard HTTPS fetch still fails certificate validation locally; HTTP paths timed out.
- `BOP_SALAMANCA`: local parse succeeds, but the project VPS still times out at 60 seconds, so promotion remains blocked.

## Follow-up batch: TLS truststore, Cadiz, Ciudad Real, Zaragoza probe

Validated locally on 2026-06-01 as metadata-only monitors:

- `BOP_CADIZ`: official current BOP Cadiz landing page at `https://www.bopcadiz.es/`; emits bulletin-level metadata from the current landing page when the requested date matches.
- `BOP_CIUDAD_REAL`: official date-scoped page at `https://bop.dipucr.es/bop/{yyyy}/{mm}/{dd}`; emits announcement metadata and stores PDF endpoints only as official metadata with `pdf_endpoint_not_downloaded`.

Probed locally but not promoted:

- `BOP_ZARAGOZA`: official BOPZ latest-bulletin page at `https://boletin.dpz.es/BOPZ/`; the local parser emits edict metadata, but the project VPS timed out connecting to the official endpoint. Registry status remains `inventory_only`.

The HTML monitor now uses Python `truststore` for TLS verification when available, falling back to
the default SSL context. This fixes official sites whose certificates validate through the system
trust store without disabling TLS verification.

Local live preview evidence:

- `BOP_CADIZ` for `2026-06-01`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=128.091`, `issue_number=102`.
- `BOP_CIUDAD_REAL` for `2026-06-01`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=7569763`, `issue_number=102`.
- `BOP_ZARAGOZA` local-only probe for `2026-06-01`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=892129`, `issue_number=122`; VPS validation failed with a connection timeout.

Registry impact after this batch:

- `monitor_validated`: 48
- `inventory_only`: 8
- provincial `inventory_only`: 5
- normal next-source ranking: `BOP_ZARAGOZA`, `BOP_CUENCA`, `BOP_OURENSE`, `BOP_SALAMANCA`.

Still deferred after this batch:

- `BOP_ALMERIA`: official surface remains ZK/JavaScript; plain GET does not expose deterministic bulletin records.
- `BOP_OURENSE`: portal request succeeds with system trust, but a deterministic bulletin-record path still needs source-specific probing.
- `BOP_SALAMANCA`: local parse succeeds, but the project VPS still times out at 60 seconds, so promotion remains blocked.
- `BOP_ZARAGOZA`: local parser succeeds, but the project VPS cannot connect to `boletin.dpz.es:443`.

## Follow-up batch: Ourense API and Cuenca WAF diagnosis

Validated locally and on the project VPS on 2026-06-01 as metadata-only API monitor:

- `BOP_OURENSE`: official Angular portal backing endpoint at `https://bop.depourense.es/portalapi/api/boletin/getFecha/{yyyymmdd}`. The endpoint returns bulletin and edict metadata as JSON. Edict HTML endpoints are stored as official metadata only.

Diagnosed but not promoted:

- `BOP_CUENCA`: official date-scoped Liferay BOP page parses locally with browser-compatible headers, but the project VPS is rejected by the official `volt-adc` WAF with `403 Forbidden`. Registry status remains `inventory_only`.

Live preview evidence for `2026-06-01`:

- `BOP_OURENSE`: `records=1`, `candidate_status=not_candidate`, `evidence_status=not_evidence`, first `document_id=351132`, `issue_number=101`.

Registry impact after this batch:

- `monitor_validated`: 50
- `inventory_only`: 6
- provincial `inventory_only`: 3
- normal next-source ranking: `BOP_ZARAGOZA`, `BOP_CUENCA`, `BOP_SALAMANCA`.

Still deferred after this batch:

- `BOP_CUENCA`: local parser succeeds, but the project VPS is rejected by the official WAF.
- `BOP_SALAMANCA`: local parse succeeds, but the project VPS still times out at TCP/TLS connection to the official sede.
- `BOP_ZARAGOZA`: local parser succeeds, but the project VPS times out at TCP connection to `boletin.dpz.es:443`.

## Follow-up implementation: BOP_ALMERIA ZK metadata monitor

Validated on 2026-06-01 that `BOP_ALMERIA` does not require Playwright for metadata discovery.
The official ZK page can be initialized with `httpx` by requesting `publicoValidar.zul` with the
same public `p=dipalme` parameters used by the browser, extracting `dtid` and the public window
UUID from the bootstrap page, and replaying the read-only `/bop/zkau` `echo` request for
`onAfterComposeNinguna`.

Live preview evidence for `2026-06-01`:

- `BOP_ALMERIA`: `records=3` with `--limit 3`, `candidate_status=not_candidate`,
  `evidence_status=not_evidence`, first `document_id=1488-2026`, `issue_number=2026/103`.

Registry impact:

- `BOP_ALMERIA` is now `monitor_validated` with `monitor_support=available`.
- The monitor remains metadata-only: no candidates, evidence-grade records, PDFs/artifacts,
  backfill, downstream writes, Hermes, systemd, or timer changes were introduced.
- Per-announcement official URLs were not exposed by the ZK listing response; records therefore
  carry `official_url=null` and `entry_hash_fallback_missing_official_url`.

## Follow-up probe: alternate feed and sitemap routes for VPS-blocked sources

Checked from the project VPS on 2026-06-01 before considering any proxy/relay workaround:

- `BOP_CUENCA`: `/rss`, `/rss.xml`, `/sitemap.xml`, `/boletin-oficial-de-la-provincia/rss`, `/boletin-oficial-de-la-provincia/rss.xml`, and `/o/rss` all returned `403` from `volt-adc` on the VPS. Local `sitemap.xml` exists, but it is inside the same WAF perimeter and is not usable from the VPS.
- `BOP_ZARAGOZA`: `boletin.dpz.es` and `www.dpz.es` RSS/sitemap candidates timed out from the VPS.
- `BOP_SALAMANCA`: `sede.diputaciondesalamanca.gob.es` RSS/sitemap candidates timed out from the VPS. `www.lasalina.es` RSS/sitemap candidates were reachable but returned `404`, so they are not an alternate bulletin feed.

Registry impact:

- `BOP_CUENCA`, `BOP_SALAMANCA`, and `BOP_ZARAGOZA` now carry `blocked_vps: true`
  and `pending_relay: true`.
- They remain `inventory_only`; no candidates, evidence-grade records, PDFs/artifacts, backfill, downstream writes, Hermes, systemd, or timer changes were introduced.

## Deferred

- BORME: defer for this project unless scoped to a metadata-only spike. External parsers are not a direct fit for the current licensing and artifact-boundary constraints.

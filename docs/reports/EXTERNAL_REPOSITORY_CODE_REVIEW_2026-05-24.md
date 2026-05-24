# External Repository Code Review

Date: 2026-05-24

Scope: review selected public GitHub repositories for patterns that may help `official-sources`.

This is a report-only review. No code was imported, no VPS operation was run, no DB was touched, and no artifacts were downloaded.

## Repositories Reviewed

| Repository | Commit inspected | Primary stack | Direct fit |
|---|---:|---|---|
| [carm-es/BORM](https://github.com/carm-es/BORM) | `e66f503` | Java/JAX-WS | Low |
| [zaragoza-sedeelectronica/ext.contratacion](https://github.com/zaragoza-sedeelectronica/ext.contratacion) | `4a562b0` | Java/Spring/Oracle | Medium, separate contracts track |
| [AxierSangroniz/bop_valladolid_IA](https://github.com/AxierSangroniz/bop_valladolid_IA) | `c71c9e0` | Python/scripts | Medium, BOP endpoint discovery |
| [AxierSangroniz/bop-valladolid-pipeline](https://github.com/AxierSangroniz/bop-valladolid-pipeline) | `995641c` | Python/scripts | Medium, BOP endpoint discovery |
| [xavimf87/mcp-govern](https://github.com/xavimf87/mcp-govern) | `8f0246b` | Python/FastMCP | Medium, MCP/rate-limit reference |
| [AlbertoUAH/datos-gob-es-mcp](https://github.com/AlbertoUAH/datos-gob-es-mcp) | `c48def6` | Python/FastMCP | Medium, MCP aggregator/reference |
| [girdeux31/oposGV](https://github.com/girdeux31/oposGV) | `4e9bfcb` | Python/PDF parsing | Low for `official-sources`; possible downstream `oposiciones2.0` reference |
| [erral/kontrata-react](https://github.com/erral/kontrata-react) | `b2267bc` | React/Elastic | Low for ingestion; useful contracts UI reference |

## Executive Result

We can advance, but not by unblocking BORM PDFs through `carm-es/BORM`.

Best actionable follow-up:

```text
TASK-BOP-VALLADOLID-001 — BOP Valladolid endpoint fixture discovery
```

Reason:

```text
The Valladolid repositories reveal a concrete BOP date URL pattern and section/document parsing strategy.
They are PDF-first and commercial/LLM-oriented, so they should not be imported directly.
But they are useful prior art for a metadata-only provincial source audit.
```

Recommended sequencing:

```text
1. Keep BORM evidence paused.
2. Run BOA 30-day metadata backfill next if continuing autonomous sources.
3. In parallel, start BOP Valladolid endpoint discovery as a docs/local task.
4. Keep MCP external repos as architecture references only.
```

## Findings

### 1. `carm-es/BORM`

Finding:

```text
Not useful for BORM bulletin PDF access.
```

Evidence from code:

```text
artifactId=ActualizaFirmaWS
JAX-WS endpoint=/services/ActualizaFirmaWS
AFIRMA / RedSARA signature update endpoints
resources=firmaCADES.xml, firmaPADES.xml, firmaXADES.xml
```

Assessment:

This is a BORM-related signature update service, not the public BORM bulletin portal, not a PDF delivery service, and not a source of announcement metadata endpoints. It contains BORM application identifiers such as `carm.web_borm` and `carm.borm.anuncios`, but no public `services/anuncio/.../pdf` access solution.

Impact for current blocker:

```text
BORM PDF evidence remains blocked by PerfDrive/Radware from VPS.
This repo does not provide a safe official alternative endpoint.
```

Recommendation:

```text
Do not use this repo to continue BORM evidence download.
Keep BORM evidence flow paused unless an official non-PerfDrive artifact route is found.
```

### 2. BOP Valladolid repositories

Repositories:

```text
AxierSangroniz/bop_valladolid_IA
AxierSangroniz/bop-valladolid-pipeline
```

Useful code-derived endpoint pattern:

```text
BASE_URL=https://bop.sede.diputaciondevalladolid.es/ultimobop
date parameter=_BOPVisualizaBoletin_WAR_BOPVisualizaBoletin_fecha=YYYY-MM-DD
portal component=BOPVisualizaBoletin_WAR_BOPVisualizaBoletin
```

Useful parsing hints:

```text
list container=#listado_anuncios ul.listado_anuncios or ul.listado_anuncios
section node class=una_seccion
document node class=un_anuncio
section title=III.-ADMINISTRACION LOCAL
PDF links selected via a[title*='pdf' i][href]
stable document id inferred from filenames like BOPVA-A-YYYY-NNNNN.pdf
```

Limits:

```text
PDF-first
downloads artifacts by design
uses mutable local JSON state
classification is LLM/commercial-lead oriented
not metadata-only
not designed for official source integrity/citation model
```

Fit for `official-sources`:

```text
Good as endpoint discovery prior art.
Not suitable for direct code reuse.
```

Recommendation:

Create a new docs/local discovery task for BOP Valladolid:

```text
TASK-BOP-VALLADOLID-001 — BOP Valladolid endpoint fixture discovery
```

Scope:

```text
no VPS
no DB
no candidates
no PDF bulk download
test a few dates only
document date-to-issue, issue ID, document IDs, HTML/PDF availability, no-publication behavior
```

### 3. `mcp-govern`

Finding:

```text
Useful MCP and public-data client reference, but not a replacement for official-sources architecture.
```

Useful patterns:

```text
central async HTTP helper
domain concurrency limit
retry on 429/5xx
explicit User-Agent
FastMCP tool descriptions with routing instructions
BDNS endpoints documented for convocatorias and concesiones
BOE/BORME summary endpoints use BOE open-data API
Socrata dataset identifiers documented for Catalonia contracts/subsidies
```

Risks if copied directly:

```text
live-query MCP surface
investigative/corruption-oriented semantics
tool output optimized for interactive answers, not evidence storage
no official_documents/document_files/ingestion_runs model
```

Fit:

```text
Reference only.
Useful for rate-limit/client design and future read-only MCP descriptions.
```

Recommendation:

Do not import tools. Extract only design lessons:

```text
explicit User-Agent
per-domain concurrency
retry/backoff discipline
clear tool routing text
facts vs indicators separation for investigative outputs
```

### 4. `datos-gob-es-mcp`

Finding:

```text
Useful reference for MCP aggregation and datos.gob.es/BOE clients.
```

Useful patterns:

```text
FastMCP subservers per source
aggregator that proxies downstream MCP tools
connection pooling
HTTP/2 option
retry/backoff
dataset search cache
BOE Accept header handling for JSON/XML
BOE summary/document/BORME methods
```

Risks if copied directly:

```text
MCP-first architecture
semantic search/cache behavior unsuitable as source-of-record evidence
some README claims are product-facing and should not drive official compliance claims
BOE search method appears exploratory, not a validated ingestion contract
```

Fit:

```text
Reference only for MCP ergonomics and aggregator mechanics.
Not an ingestion source for official-sources.
```

Recommendation:

Use as comparison material for:

```text
tools/list naming
tool descriptions
aggregated MCP surface design
HTTP client pooling/rate limiting
```

Keep `official-sources` storage-first:

```text
storage -> source adapter -> normalization -> CLI/API -> read-only MCP
```

### 5. `zaragoza-sedeelectronica/ext.contratacion`

Finding:

```text
Relevant for a future public-procurement track, not for current ayudas/bulletin flow.
```

Useful code areas:

```text
ContratoOCDSController
ContratoController
ApiTramitaController
IntegracionPlataformaEstado/CodiceConverter*
JSON-LD / RDF / Turtle / XML / CSV output support
OCDS-related contract modeling
```

Limits:

```text
large legacy Java/Oracle application
old upload-style public repo
not a crawler/client for external public contract data
not directly reusable in Python official-sources
```

Fit:

```text
Medium for future contracts normalization, low for immediate official bulletin work.
```

Recommendation:

Defer. If contracts become a product line, create a separate task:

```text
TASK-CONTRACTS-001 — Review Zaragoza OpenCity/OCDS model for procurement source schema
```

Do not mix this into BOCYL/BOPV/BORM/BOA bulletin pipeline.

### 6. `erral/kontrata-react`

Finding:

```text
Frontend search reference for indexed procurement data.
```

Useful patterns:

```text
Elastic-backed faceted search
Basque contracts domain
filters by authority, status, contract type, date, price, budget, minor contract
multilingual UI
```

Limits:

```text
frontend only
requires pre-indexed Elastic data
README mentions CORS bypass extension, unsuitable for production/integration guidance
not an ingestion/evidence pipeline
```

Fit:

```text
Low for official-sources ingestion.
Potential UI inspiration for a future procurement explorer.
```

Recommendation:

Defer.

### 7. `girdeux31/oposGV`

Finding:

```text
Useful as a narrow GVA PDF parsing example, not as official-sources source adapter.
```

Useful patterns:

```text
GVA root URL=https://ceice.gva.es/auto/Actas
BeautifulSoup navigation over indexcolname table cells
PDF caching by local path
pdftotext-based parsing with pinned version
tests with reference PDFs
```

Limits:

```text
domain is education/public exam results, not official bulletin metadata
downloads and parses PDFs directly
no official source integrity model
not a generalized DOGV/official bulletin source
```

Fit:

```text
Low for official-sources.
Possible downstream reference for oposiciones2.0 only.
```

Recommendation:

Do not use for current official-sources roadmap. Mention as possible future `oposiciones2.0` research input.

## Prioritized Next Steps

### Immediate

Continue with the next already prepared metadata operation:

```text
TASK-AUTO-BOA-003 — Controlled BOA 30-day metadata backfill
```

Reason:

```text
BORM evidence is blocked.
BOA is already in the autonomous-source flow and should advance metadata-only.
```

### Parallel Docs/Research

Start:

```text
TASK-BOP-VALLADOLID-001 — BOP Valladolid endpoint fixture discovery
```

Suggested prompt:

```text
Objective: audit BOP Valladolid as a future provincial metadata-only source.
Use the public endpoint pattern observed in AxierSangroniz/bop_valladolid_IA and bop-valladolid-pipeline.
Do not download PDFs in bulk.
Do not create candidates.
Do not touch VPS.
Test only a few dates.
Document date URL, section parsing, document IDs, PDF/HTML availability, no-publication behavior, risks and MVP feasibility.
```

### Deferred

```text
TASK-CONTRACTS-001 — Procurement/OCDS source family review
```

Inputs:

```text
zaragoza-sedeelectronica/ext.contratacion
erral/kontrata-react
mcp-govern PSCP/datos.gob references
```

### Not Recommended Now

```text
Do not resume BORM evidence download based on carm-es/BORM.
Do not copy MCP live-query designs into official-sources ingestion.
Do not import BOP Valladolid PDF/LLM pipeline code directly.
```

## Bottom Line

The reviewed repositories do help, but mainly by clarifying what to do next:

```text
BOA remains the best immediate VPS operation.
BOP Valladolid is now a good provincial endpoint-discovery candidate.
BORM evidence should stay paused.
MCP repos are architecture references, not ingestion sources.
Procurement repos belong to a separate future contracts track.
```

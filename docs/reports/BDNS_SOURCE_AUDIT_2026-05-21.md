# BDNS Source Audit

Date: 2026-05-21

## Summary

BDNS / SNPSAP is viable and strategically important for `official-sources`.

Unlike BOE, BOJA, DOGV, and BOCM, BDNS is not primarily a bulletin source. It is an official
registry for grants, subsidies, public aid calls, and awards. For downstream projects such as
EduAyudas, `la-ayuda`, and future subsidy-focused products, BDNS should be treated as a primary
grants source rather than only supporting bulletin evidence.

Recommendation:

```text
Implement TASK-BDNS-002 as a metadata-only adapter MVP.
```

## Sources Reviewed

Official sources:

- <https://www.infosubvenciones.es/bdnstrans/GE/es/index>
- <https://www.infosubvenciones.es/bdnstrans/doc/swagger>
- <https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/AYUDA%20-%20Sistema%20Nacional%20de%20Publicidad%20de%20Subvenciones%20y%20Ayudas%20P%C3%BAblicas%20v2023.pdf>
- <https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal>

Reference repository reviewed:

- <https://github.com/mjgmario/spanish-public-info-radar-mcp>
- `src/public_radar/sources/bdns.py`

Safe manual endpoint probes were run against official BDNS JSON endpoints with page size 2. No DB
writes, candidate creation, artifact downloads, or downstream writes were performed.

## Official API Status

The official SNPSAP help document states that the portal offers automated integration through a REST
API for JSON data, that access is public, and that the technical Swagger documentation is published
at `/bdnstrans/doc/swagger`.

Observed behavior:

- `/bdnstrans/doc/swagger` currently serves the SPA shell from the public portal.
- The JSON API endpoints are directly callable under `/bdnstrans/api`.
- Responses are paginated JSON with `content`, `pageable`, `totalElements`, `totalPages`, `size`,
  `number`, and `advertencia`.

## Endpoints Probed

Base URL:

```text
https://www.infosubvenciones.es/bdnstrans/api
```

### Latest Convocatorias

```text
GET /convocatorias/ultimas?page=1&pageSize=2
```

Observed:

```text
status=200
content_type=application/json
response_shape=page
items_key=content
sample_identifier_fields=id,numeroConvocatoria
```

Use:

```text
latest registered grant calls
```

### Convocatorias Search

```text
GET /convocatorias/busqueda?page=1&pageSize=2
GET /convocatorias/busqueda?page=1&pageSize=2&fechaDesde=20/05/2026&fechaHasta=20/05/2026
```

Observed:

```text
status=200
content_type=application/json
response_shape=page
items_key=content
date_format=DD/MM/YYYY
sample_identifier_fields=id,numeroConvocatoria
```

Use:

```text
filtered grant call search
```

### Convocatoria Detail

```text
GET /convocatorias?numConv=907042
```

Observed:

```text
status=200
content_type=application/json
response_shape=object
identifier_field=codigoBDNS
internal_id_field=id
```

Important detail:

```text
GET /convocatorias/{id}
GET /convocatorias/{numeroConvocatoria}
```

both returned `404` in the manual probe. The reliable detail lookup observed in this audit is the
query-parameter form:

```text
GET /convocatorias?numConv=<codigoBDNS>
```

### Concesiones Search

```text
GET /concesiones/busqueda?page=1&pageSize=2
GET /concesiones/busqueda?page=1&pageSize=2&fechaDesde=20/05/2026&fechaHasta=20/05/2026
```

Observed:

```text
status=200
content_type=application/json
response_shape=page
items_key=content
sample_identifier_fields=id,codConcesion
convocatoria_link_fields=numeroConvocatoria,idConvocatoria
amount_fields=importe,ayudaEquivalente
```

Use:

```text
filtered award search
```

## Data Types Available

BDNS exposes at least these useful public data types:

- `convocatorias`: grant/subsidy calls.
- `concesiones`: awards linked to calls and beneficiaries.
- public call detail by BDNS number.
- public web routes for call pages and concession views.

The public help document also describes other portal areas such as state aid, de minimis aid, large
beneficiaries, political parties, and strategic subsidy plans. Those should be deferred until after a
convocatorias/concesiones MVP.

## Identifier Strategy

Recommended convocatoria identifiers:

```text
source_code=BDNS
resource_type=grant_call
official_identifier=BDNS-<codigoBDNS>
bdns_code=<codigoBDNS or numeroConvocatoria>
bdns_internal_id=<id>
```

Rationale:

- list endpoints expose `numeroConvocatoria`;
- detail endpoint exposes `codigoBDNS`;
- both represent the public BDNS call number;
- `id` is useful for internal linking but should not be the primary external identifier.

Recommended concesion identifiers:

```text
source_code=BDNS
resource_type=grant_award
official_identifier=BDNS-CONCESION-<codConcesion or id>
bdns_award_code=<codConcesion>
bdns_award_id=<id>
bdns_call_code=<numeroConvocatoria>
bdns_call_internal_id=<idConvocatoria>
```

For citation, prefer the public BDNS call code and SNPSAP/BDNS as source name.

## Field Observations

Convocatoria list item fields observed:

```text
id
mrr
numeroConvocatoria
descripcion
descripcionLeng
fechaRecepcion
nivel1
nivel2
nivel3
codigoInvente
```

Convocatoria detail fields observed:

```text
id
organo
sedeElectronica
codigoBDNS
fechaRecepcion
instrumentos
tipoConvocatoria
presupuestoTotal
mrr
descripcion
descripcionLeng
tiposBeneficiarios
sectores
regiones
descripcionFinalidad
descripcionBasesReguladoras
urlBasesReguladoras
sePublicaDiarioOficial
abierto
fechaInicioSolicitud
fechaFinSolicitud
documentos
anuncios
advertencia
```

Concesion list item fields observed:

```text
id
codConcesion
fechaConcesion
beneficiario
instrumento
importe
ayudaEquivalente
urlBR
tieneProyecto
numeroConvocatoria
idConvocatoria
convocatoria
descripcionCooficial
nivel1
nivel2
nivel3
codigoInvente
idPersona
fechaAlta
```

## API Quirks

Practical quirks to handle in an adapter:

- Dates for search filters use Spanish format: `DD/MM/YYYY`.
- List response items use `numeroConvocatoria`, while detail uses `codigoBDNS`.
- The reliable detail lookup observed is `/convocatorias?numConv=<codigoBDNS>`, not
  `/convocatorias/{id}`.
- Response pages use `content`; older or external-reference code should still tolerate `items`.
- Amount fields vary by domain: `presupuestoTotal` for calls, `importe` and `ayudaEquivalente` for
  awards.
- Date fields vary by domain: `fechaRecepcion`, `fechaInicioSolicitud`, `fechaFinSolicitud`,
  `fechaConcesion`, and `fechaAlta`.
- Text fields can be multilingual: `descripcion` and `descripcionLeng`.
- Some URLs point outside BDNS, for example `sedeElectronica`, `urlBasesReguladoras`, and `urlBR`.
- The official portal warns that public results can change over time, especially dynamic permalinks
  and time-limited public concession visibility.
- Public data reuse has source citation and metadata-preservation requirements.
- Requests are traced by the public system according to the official help document.

## Pagination Behavior

Observed list endpoints return Spring-style pagination:

```text
content
pageable
last
totalElements
totalPages
first
sort
numberOfElements
size
number
empty
advertencia
```

MVP pagination should:

- use small/conservative page sizes by default;
- store page-level raw response hashes;
- stop by `last=true`, `empty=true`, or `numberOfElements=0`;
- cap pages for early pilots;
- never silently ignore partial failures.

## Comparison With spanish-public-info-radar-mcp

The external repository correctly identifies the core BDNS surfaces:

```text
/convocatorias/ultimas
/convocatorias/busqueda
/concesiones/busqueda
```

Useful ideas:

- source-specific BDNS client/parser;
- Spanish date formatting before request dispatch;
- tolerance for both `content` and `items`;
- ID fallback handling;
- Decimal parsing for money fields;
- separated parsing for convocatorias and concesiones.

Local differences for `official-sources`:

- do not use live MCP calls as the primary runtime model;
- keep cache-first evidence storage;
- hash raw official payloads before parsing;
- preserve citation and integrity metadata;
- keep downstream publication decisions outside `official-sources`;
- do not expose beneficiary/concession data without a privacy-aware review step.

No code was copied from the external repository.

## Recommended Data Model

BDNS should be modeled as:

```text
source family: grants_registry
role: primary grants/subsidies source
candidate source: yes, after metadata MVP and review
supporting evidence source: yes, for BOE/autonomous bulletin evidence
bulletin source: no
```

Recommended storage strategy for MVP:

- add official source `BDNS`;
- reuse `official_documents` only if the current schema can represent non-bulletin grant registry
  records without weakening semantics;
- otherwise add a narrowly scoped generic official records layer before implementation;
- use `resource_type` values such as `grant_call` and `grant_award`;
- store raw page/detail JSON hashes;
- preserve official public URLs and external application/base-regulation URLs;
- preserve citation JSON.

Do not force BDNS records into bulletin terminology such as issue numbers or daily summaries.

## Expected Adapter Complexity

```text
complexity=medium
priority=P1
```

Why not low:

- BDNS is semantically different from bulletin sources.
- Convocatorias and concesiones need different identifiers and parser logic.
- Awards may include personal data or partially masked identifiers.
- Public visibility and retention rules matter for concessions.
- Field names vary across list/detail/award endpoints.

Why not high:

- official JSON endpoints are directly available;
- pagination is conventional;
- date filtering is straightforward;
- convocatoria detail by `numConv` is stable in manual probes;
- no date-to-issue discovery is required.

## Recommended MVP Scope

Recommended next task:

```text
TASK-BDNS-002 — BDNS metadata adapter MVP
```

MVP scope:

```text
source record BDNS
convocatorias search by date range
latest convocatorias endpoint, limited
convocatoria detail by numConv
raw JSON hash before parsing
pagination with strict page cap
official identifiers and citation metadata
preserve public BDNS/detail URLs
preserve application/base-regulation URLs
ingestion_run audit
no candidates
no downstream
no publication
```

Defer:

```text
concesiones ingestion
beneficiary search
state aid / de minimis variants
bulk historical backfills
candidate extraction
downstream exports
MCP tools
```

Concesiones are valuable, but should be a second phase because they need stricter privacy and
retention handling.

## Risks

- Official Swagger access is routed through the portal SPA; implementation should be based on
  endpoint probes and fixtures, with documentation links retained.
- BDNS is not a bulletin, so schema semantics need care.
- Public concession data can include beneficiary names or masked personal identifiers.
- Public concession visibility has time limitations and privacy restrictions.
- Dynamic public links can produce different results over time.
- Field naming varies across endpoints and may change.
- Bulk pagination could be large; early runs need page/date caps.
- BDNS should not be treated as approval for downstream publication.

## Decision

BDNS should be implemented before further low-value bulletin expansion for subsidy-focused
downstreams.

Proceed with:

```text
TASK-BDNS-002 — BDNS metadata adapter MVP
```

Do not implement candidate extraction or downstream import until BDNS metadata ingestion has a
small verified pilot with raw hashes, citation, and integrity behavior.

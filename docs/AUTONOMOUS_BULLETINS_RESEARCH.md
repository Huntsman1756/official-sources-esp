# Autonomous Bulletins Research

Autonomous bulletin adapters are not implemented in MVP-001. Each bulletin needs its own source assessment, parser design, tests, integrity semantics, and citation rules.

RSS availability does not imply stable parsing. Autonomous bulletins are not technically homogeneous.

Latest audit:

- `docs/reports/AUTONOMOUS_BULLETIN_SOURCE_AUDIT_2026-05-20.md`

| source_code | source_name | jurisdiction | official_url | has_api | has_rss | has_html | has_xml | has_pdf | stable_ids | search_available | robots_notes | adapter_complexity | recommended_priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOJA | Boletin Oficial de la Junta de Andalucia | ES-AN | https://www.juntadeandalucia.es/boja | yes | not confirmed | yes | unknown | yes | yes | yes | must be reviewed | low | P1 | Recommended first adapter. Official OpenAPI is available at `https://datos.juntadeandalucia.es/api/v0/boja/openapi.json`. |
| BOCM | Boletin Oficial de la Comunidad de Madrid | ES-MD | https://www.bocm.es | no formal API found | yes | yes | yes, summary XML | yes | yes | yes | must be reviewed | low-medium | P1/P2 | Strong second candidate. RSS, current issue XML, recent summary RSS, issue HTML, and deterministic PDF paths were observed. |
| DOGV | Diari Oficial de la Generalitat Valenciana | ES-VC | https://dogv.gva.es | no formal OpenAPI found | not confirmed | yes | yes, per official FAQ | yes | yes | yes | must be reviewed | medium | P2 | Good candidate after endpoint discovery. Official FAQ says HTML, PDF, and ELI XML are available; portal routes need hardening. |
| BOME | Boletin Oficial de Melilla | ES-ML | https://bomemelilla.es | partial, undocumented site endpoints | not confirmed | yes | not found | yes | yes | yes | must be reviewed | medium-high | P3 | Official naming confirmed as BOME. Issue and article CVEs are stable, but API/calendar endpoints are undocumented. |
| BOCCE | Boletin Oficial de la Ciudad de Ceuta | ES-CE | https://www.ceuta.es/ceuta/bocce | no | not found | yes | not found | yes | partial | partial | must be reviewed | high | defer | Defer until after one cleaner autonomous adapter. Joomla/JDownloads structure and PDF-first behavior need careful fixtures. |

Before implementation, update the target source row with verified endpoint examples, stable identifier strategy, robots/terms notes, rate-limit assumptions, and fixture samples.

Recommended next adapter MVP:

```text
TASK-AUTO-002 - BOJA adapter MVP
```

TASK-AUTO-002 status: implemented as a metadata/date MVP.
TASK-AUTO-002B status: pagination and completeness guard implemented.

Implemented scope:

- official API endpoint `/api/v0/boja/get/search_pagination`;
- one-date ingestion through `official-sources ingest-boja-date --date YYYY-MM-DD`;
- all-page ingestion for one date using BOJA `total_hits` as the completeness target;
- CLI reporting of `pages_fetched` and `pagination_complete`;
- max-page safety through `OFFICIAL_SOURCES_BOJA_MAX_PAGES_PER_DATE` with default `20`;
- stable external IDs prefixed as `BOJA:<api_id>`;
- `publicUrl` preservation;
- `pathPdf` preservation as metadata only;
- raw JSON payload hash stored as `source_snapshot_hash`;
- deterministic combined raw payload hash for multi-page responses;
- ingestion run audit for success and empty/no-publication dates.

Completeness policy:

- `total_hits=0` with empty results is `no_publication`;
- missing `total_hits` is ambiguous and fails the ingestion;
- reaching the max-page limit before collecting `total_hits` fails the ingestion;
- incomplete runs must not silently store page 0 as complete.

Still excluded:

- candidate extraction;
- downstream writes;
- PDF downloads by default;
- text extraction;
- legal interpretation;
- generic all-autonomous framework.

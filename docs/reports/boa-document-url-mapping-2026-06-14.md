# BOA Document URL Mapping Verification

Date: 2026-06-14
Task: `TASK-OFFICIAL-SOURCES-BOA-DOCUMENT-URL-MAPPING-001`

## Scope

Verify the BOA document-level official URL mapping after the metadata catch-up.

This was a read-only verification task. It did not modify parser code, runtime config, systemd,
SQLite data, candidates, evidence-grade records, artifacts, downstream projects, drafts, or
publications.

## Reason

The BOA metadata catch-up report initially recorded an activation gap because a post-check looked
for the confirmed `MLKOB` value in `official_documents.url_html`. BOA stores the official document
object URL in `url_pdf`, not `url_html`, because the upstream JSON exposes document object links via
`UrlPdf`.

## Runtime Context

```text
vps=mcpspain-official-sources-vps
app=/opt/official-sources/app
db=/opt/official-sources/data/official_sources.sqlite
head=bdddd07
```

Live parser probe:

```text
BOA_OFFICIAL_URL_RE = re.compile(r"https://www\.boa\.aragon\.es/cgi-bin/EBOA/BRSCGI\?[^`´\s]+")
document_pdf_url = _first_official_url(record.get("UrlPdf"))
url_pdf=document_pdf_url
sample_extraction=https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VEROBJ&MLKOB=1451277650606
```

## Verification

```text
boa_documents_total=1384
boa_url_pdf_present=1384
boa_url_html_present=0
boa_url_xml_present=0
boa_comedor_pdf_sample=1
boa_pdf_missing_but_raw_urlpdf_present=0
```

Confirmed EduBecas comedor sample rows:

```text
BOA:007958917
publication_date=2026-06-05
url_pdf=https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VEROBJ&MLKOB=1451277650606
url_html=None
url_xml=None

BOA:007958933
publication_date=2026-06-05
url_pdf=https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VEROBJ&MLKOB=1451309970808
url_html=None
url_xml=None
```

## Decision

```text
TASK-OFFICIAL-SOURCES-BOA-DOCUMENT-URL-MAPPING-001: DONE
Validation: GO
Parser changes: 0
VPS DB writes: 0
source_candidates writes: 0
artifact/PDF downloads: 0
downstream writes: 0
runtime/systemd/timer changes: 0
```

The BOA URL mapping is adequate for the current metadata-only upstream contract:

- `url_pdf` contains the official BOA `VEROBJ` document object URL;
- `url_html` and `url_xml` remain empty because the date JSON does not provide those endpoints;
- no document with raw `UrlPdf` evidence is missing persisted `url_pdf`.

Next BOA work should move to candidate dry-run quality, not URL mapping.

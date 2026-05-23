# BDNS Latest Ingestion Preflight

Date: 2026-05-21

## Summary

TASK-BDNS-003-PREP rehearsed the BDNS latest-call ingestion locally against a temporary SQLite
database only.

Scope observed:

```text
convocatorias only
metadata only
latest calls with limit=5
one detail lookup for a returned codigoBDNS
temporary local SQLite database
no VPS connection
no production database write
no source candidates
no downstream writes
no document/PDF downloads
no concesiones ingestion
```

## Local Rehearsal

Temporary database:

```text
C:\Users\rome_\AppData\Local\Temp\bdns-preflight-cfb0ce3x\bdns-preflight.sqlite
```

Latest-call command:

```bash
official-sources --db-path <temp-db> ingest-bdns-latest --limit 5
```

Result:

```text
status=success
bdns_result=success
documents_fetched=5
documents_new=5
documents_updated=0
page_count=1
pagination_limit_reached=false
sample_identifiers=BDNS:907637,BDNS:907636,BDNS:907635,BDNS:907634,BDNS:907628
retry_count=0
throttle_triggered=0
last_http_status=200
source_snapshot_hash=ce25298a85abcf96a1ebde1a1b2eaf704aa87889f5f712113c18d6343ee1cb03
```

Detail command:

```bash
official-sources --db-path <temp-db> ingest-bdns-call --num-conv 907637
```

Result:

```text
status=success
bdns_result=success
official_identifier=BDNS:907637
documents_fetched=1
documents_new=0
documents_updated=1
page_count=1
pagination_limit_reached=false
sample_identifiers=BDNS:907637
retry_count=0
throttle_triggered=0
last_http_status=200
source_snapshot_hash=95bea5deae53a481a9bbcead15b015b57c62d6de7f0b3106eb0e2254b2b217fe
```

Database validation:

```text
status=valid
current_version=8
latest_version=8
```

## Temporary DB Counts

After latest ingestion plus one detail lookup:

```text
BDNS official_documents=5
raw_api_response document_files=6
source_candidates=0
artifact_download_attempts=0
concesiones metadata mentions=0
```

Stored BDNS documents:

```text
BDNS:907628 document_type=grant_call resource_type=grant_call url_pdf=null url_xml=null
BDNS:907634 document_type=grant_call resource_type=grant_call url_pdf=null url_xml=null
BDNS:907635 document_type=grant_call resource_type=grant_call url_pdf=null url_xml=null
BDNS:907636 document_type=grant_call resource_type=grant_call url_pdf=null url_xml=null
BDNS:907637 document_type=grant_call resource_type=grant_call url_pdf=null url_xml=null
```

The extra `raw_api_response` row is expected because the detail lookup stores a separate raw JSON
snapshot for `BDNS:907637`.

## Parser Observations

No parser edge case appeared during the rehearsal.

No fixture or parser test was added for this prep task.

## Recommended VPS Command

Supervisor command for TASK-BDNS-003:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite ingest-bdns-latest --limit 20
```

Recommended pre-run checks:

```text
confirm current DB backup exists
confirm command target is ingest-bdns-latest
confirm limit is explicit and <= 20
confirm no downstream/candidate/artifact commands are chained
```

Recommended post-run checks:

```text
official-sources --db-path /opt/official-sources/data/official_sources.sqlite db validate
check latest BDNS ingestion_run status=success
check source_candidates count unchanged
check artifact_download_attempts count unchanged
check inserted/updated BDNS documents have document_type=grant_call and resource_type=grant_call
check url_pdf/url_xml remain null for new BDNS records
```

## Stop Conditions

Stop and report without retrying broad ingestion if any of these occur:

```text
HTTP status is not 200
bdns_result is not success
status is failed
documents_fetched is 0 for a non-empty latest response
pagination_limit_reached is true
source_candidates count changes
artifact_download_attempts count changes
any URL or metadata indicates concesiones/concesion records
any BDNS record has url_pdf or url_xml populated by this command
db validate returns invalid
response shape causes parser failure or missing codigoBDNS/numeroConvocatoria
unexpected rate limiting, throttling, or retry behavior appears
```

## Decision

The local rehearsal supports running TASK-BDNS-003 on the VPS with the recommended bounded command,
provided the supervisor keeps the run to latest `convocatorias` metadata only and applies the stop
conditions above.

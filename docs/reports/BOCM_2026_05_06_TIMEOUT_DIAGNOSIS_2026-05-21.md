# BOCM 2026-05-06 Timeout Diagnosis

Date: 2026-05-21

## Summary

`TASK-AUTO-BOCM-003D` diagnosed the blocking BOCM date:

```text
2026-05-06
```

The failure was not a no-publication condition and not candidate/downstream related. It was a
metadata fetch reliability problem around the issue summary XML.

## Request Phase

The diagnostic split the request path into phases:

```text
search_day
summary_xml
document list parsing
```

Observed phase behavior:

| phase | URL pattern | observed result |
| --- | --- | --- |
| search_day | `/search-day-month?field_date[date]=06/05/2026` | resolved `bocm-20260506-106` |
| summary_xml | `/boletin/CM_Boletin_BOCM/2026/05/06/BOCM-20260506106.xml` | large XML, intermittent read timeout |
| document list parsing | local XML parsing after fetch | parses successfully |

The summary XML response is large:

```text
summary_xml bytes: approximately 4.15 MB
```

## Diagnosis

Classification:

```text
specific_endpoint_problem
```

The likely root cause was the BOCM summary XML fetch for a large issue. The previous generic
`fetch_issue_page` path requested the summary XML URL with an HTML-oriented `Accept` header:

```text
Accept: text/html,application/xhtml+xml
```

For the large `2026-05-06` summary XML, that path could time out before reading the response. A
direct XML-oriented request was able to retrieve the payload and parse the document list.

## Code Changes

Implemented:

- added `BOCMClient.fetch_issue_summary_xml`;
- use `Accept: application/xml,text/xml` for summary XML fetches;
- keep `Accept: text/html,application/xhtml+xml` for HTML pages;
- rename the ingestion retry/diagnostic phase from `issue_page` to `summary_xml` for summary XML;
- preserve repeated timeout behavior as `failed`, never `no_publication`.

No candidate extraction, PDF download, or downstream write path was added.

## Tests Added

Added/updated tests for:

- timeout during summary XML phase;
- diagnostics identify `summary_xml`;
- repeated timeout remains `failed`;
- successful retry stores documents once;
- no PDF document files;
- no source candidates.

## Live Smoke

Controlled local smoke after the code change:

```text
date=2026-05-06
status=success
issue_identifier=bocm-20260506-106
documents_fetched=88
documents_new=88
documents_updated=0
retry_count=0
last_http_status=200
pdf_document_files=0
source_candidates=0
artifact_download_attempts=0
```

No PDFs were downloaded. No candidates were created. No downstream project was touched.

Controlled VPS smoke after deploying commit `4952c98`:

```text
date=2026-05-06
status=failed
phase=search_day
documents_fetched=0
documents_new=0
documents_updated=0
retry_count=3
last_http_status=none
error_message=BOCM search_day request for 2026-05-06 timed out after 4 attempts: timed out
DB validation=valid
BOCM official_documents=982
BOCM PDF document_files=0
artifact_download_attempts=432
source_candidates=100
```

An immediate bounded `curl` probe against the same official search URL then returned:

```text
status=200
time=0.492620
size=24069
resolved_url=https://www.bocm.es/boletin/bocm-20260506-106
```

This means the VPS-facing failure is intermittent and can occur in the `search_day` phase before
the summary XML is requested. The local smoke proves the XML-specific request path can ingest the
date when the source responds normally, but the VPS smoke did not recover the date.

## Backfill Resume Decision

The fix was deployed to the VPS, but the scoped VPS smoke for:

```text
2026-05-06
```

did not pass. The 30-day backfill should not resume yet.

Recommended next diagnostic scope:

```text
one-date retry/probe for 2026-05-06 search_day from VPS
compare httpx vs curl behavior
avoid candidates, PDFs, and downstream
```

Follow-up status:

```text
TASK-AUTO-BOCM-003E compared curl and httpx from the VPS.
During that task curl also failed to connect, so the issue is not httpx-only.
docs/reports/BOCM_HTTPX_VS_CURL_DIAGNOSIS_2026-05-21.md records the result.
```

If that passes, the remaining metadata-only backfill can resume from:

```text
2026-05-07 -> 2026-05-20
```

Do not start BOCM candidate dry-run until the metadata-only window is complete.

## Known Limitations

- The diagnosis only addresses the summary XML fetch path.
- BOCM remains metadata-only.
- No PDFs, candidates, or downstream writes are implemented for BOCM.

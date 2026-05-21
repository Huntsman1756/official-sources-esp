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

## Backfill Resume Decision

The next step should deploy the fix to the VPS and run one scoped VPS smoke for:

```text
2026-05-06
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

# BORM PDF Access Blocker Diagnosis

Date: 2026-05-24

Task: `TASK-AUTO-BORM-008C`

Scope: diagnose the BORM PDF/HTML access blocker from the VPS and choose a safe evidence strategy.

## Current State

VPS app commit during diagnosis:

```text
843a3d0 feat: add scoped BORM artifact download
```

DB validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

Counters before and after this diagnosis:

```text
source_candidates_total=163
artifact_download_attempts=518
BORM_pdf_document_files=1
BORM_html_document_files=0
artifact_bytes=29154791
selected_review_status=human_review_required:12
```

No artifacts were downloaded by this task.

## Selected Candidates

Selected candidate IDs:

```text
151,152,153,154,155,156,157,158,159,161,162,163
```

URL availability in stored metadata:

```text
html_url=12/12
pdf_url=12/12
xml_url=0/12
```

All selected candidates remain:

```text
review_status=human_review_required
```

## PDF Probe Result

Controlled PDF probes were run against two selected official BORM PDF URLs:

```text
candidate_id=151
pdf_url=https://www.borm.es/services/anuncio/842820/pdf

candidate_id=152
pdf_url=https://www.borm.es/services/anuncio/842792/pdf
```

Observed behavior:

```text
http_status=200
redirects=1
final_host=validate.perfdrive.com
content_type=text/html; charset=UTF-8
body_title=Radware Captcha Page
```

Diagnosis:

```text
PerfDrive/Radware browser validation is confirmed for BORM PDF requests from the VPS.
The final response is not an official BORM PDF.
```

The downloader behavior from `TASK-AUTO-BORM-008B` is correct: it rejects the final non-BORM host and does not store the validation page as evidence.

## HTML Probe Result

Controlled HTML probes were run against two selected official BORM HTML URLs:

```text
candidate_id=151
html_url=https://www.borm.es/#/home/anuncio/14-05-2026/2138

candidate_id=152
html_url=https://www.borm.es/#/home/anuncio/13-05-2026/2110
```

Observed behavior:

```text
http_status=200
redirects=1
final_host=validate.perfdrive.com
content_type=text/html; charset=UTF-8
body_title=Radware Captcha Page
```

HTML evidence viability:

```text
html_evidence_viable=false
```

Reason:

```text
The retrieved HTML is a Radware validation page, not the legal publication text.
The stored BORM HTML URL is also an SPA route, and this task did not find a safe official static HTML artifact endpoint.
```

## Safe Strategy

Chosen strategy:

```text
pause_borm_evidence_flow
```

Rationale:

```text
PDF access from the VPS is blocked by PerfDrive/Radware.
HTML access from the VPS is also blocked and does not provide legal text.
Only 1 of 12 selected BORM PDFs is currently stored.
Proceeding to evidence review would create a misleading partial evidence set.
```

Explicitly not done:

```text
no PerfDrive bypass
no browser challenge automation
no rotating proxies
no unofficial mirrors
no aggressive header spoofing
no broad PDF downloads
```

## Code Changes

```text
none
```

The existing BORM downloader guardrails remain in place.

## Safety Verification

No writes during this diagnosis:

```text
artifact_download_attempts=518 -> 518
BORM_pdf_document_files=1 -> 1
BORM_html_document_files=0 -> 0
source_candidates_total=163 -> 163
selected_review_status=human_review_required:12
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener
```

## Recommendation

Do not run `TASK-AUTO-BORM-009` yet.

Recommended next task:

```text
TASK-AUTO-BOA-003 — Controlled BOA 30-day metadata backfill
```

Alternative BORM-specific follow-up, only if BORM evidence must continue:

```text
TASK-AUTO-BORM-008D — Search for official non-PerfDrive BORM evidence endpoint
```

Rules for any BORM follow-up:

```text
use only official BORM endpoints
do not bypass anti-bot protection
do not store validation HTML as evidence
keep source_candidates.review_status unchanged
```

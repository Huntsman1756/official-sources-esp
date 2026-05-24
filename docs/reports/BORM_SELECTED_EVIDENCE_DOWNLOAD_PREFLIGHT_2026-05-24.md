# BORM Selected Evidence Download Preflight

Date: 2026-05-24

Task: `TASK-AUTO-BORM-008-PREP`

Scope: prepare scoped evidence download for the BORM candidates selected by metadata-only triage.

No artifacts were downloaded. No database writes were performed. No candidate status changed. No downstream project was touched.

## Context

Latest triage report:

```text
docs/reports/BORM_30_DAY_CANDIDATE_TRIAGE_2026-05-24.md
```

Selected candidates:

```text
151,152,153,154,155,156,157,158,159,161,162,163
```

Not selected:

```text
160
```

Current state from triage:

```text
review_status=human_review_required:13
source_candidates_total=163
artifact_download_attempts=482
artifact_size=30M
DB valid
MCP privacy OK
```

## Candidate URL Availability

Read-only metadata inspection found:

```text
selected_candidates=12
html_url_available=12
xml_url_available=0
pdf_url_available=12
review_status=human_review_required:12
```

Per-candidate availability:

| candidate_id | official_identifier | publication_date | HTML URL | XML URL | PDF URL | review_status |
| ---: | --- | --- | --- | --- | --- | --- |
| 151 | `BORM:A-140526-2138` | 2026-05-14 | yes | no | yes | human_review_required |
| 152 | `BORM:A-130526-2110` | 2026-05-13 | yes | no | yes | human_review_required |
| 153 | `BORM:A-130526-2111` | 2026-05-13 | yes | no | yes | human_review_required |
| 154 | `BORM:A-120526-2086` | 2026-05-12 | yes | no | yes | human_review_required |
| 155 | `BORM:A-110526-2055` | 2026-05-11 | yes | no | yes | human_review_required |
| 156 | `BORM:A-080526-2009` | 2026-05-08 | yes | no | yes | human_review_required |
| 157 | `BORM:A-080526-2010` | 2026-05-08 | yes | no | yes | human_review_required |
| 158 | `BORM:A-080526-2011` | 2026-05-08 | yes | no | yes | human_review_required |
| 159 | `BORM:A-080526-2012` | 2026-05-08 | yes | no | yes | human_review_required |
| 161 | `BORM:A-230426-1782` | 2026-04-23 | yes | no | yes | human_review_required |
| 162 | `BORM:A-210426-1745` | 2026-04-21 | yes | no | yes | human_review_required |
| 163 | `BORM:A-210426-1746` | 2026-04-21 | yes | no | yes | human_review_required |

## Evidence Type Decision

Preferred order in principle:

```text
1. HTML if official, stable and contains full publication text
2. XML if official and parseable
3. PDF only if HTML/XML are missing or insufficient
```

BORM-specific finding:

```text
stored HTML URL = official BORM SPA route
stored XML URL = absent
stored PDF URL = official BORM PDF service URL
```

Recommendation:

```text
Do not download yet.
Implement scoped BORM downloader support first.
Prefer HTML only if the implementation verifies that the stored BORM HTML route returns full reviewable legal text, not just an Angular app shell.
If HTML is not full text, use PDF for the first evidence download because it is the only currently stored full-document official URL type.
XML is not available in current BORM candidate metadata and should not be invented.
```

Practical first implementation target:

```text
types=html,pdf support in code
first operational run likely types=pdf unless an HTML full-text probe passes
```

## Downloader Support Status

Current CLI help:

```text
usage: official-sources download-source-artifacts --source {BOE,BOJA,DOGV,BOCYL}
```

Current status:

```text
borm_downloader_supported=false
download-source-artifacts --source BORM unsupported
download-boe-artifacts --source BORM unsupported
no BORMArtifactDownloader
no BORM_ARTIFACT_FIELDS
no BORM artifact URL validator
no BORM-specific candidate-id guardrails
```

The generic downloader fallback would use BOE behavior if reached, but BORM cannot reach that path because argparse rejects `--source BORM`. A future implementation must not rely on the BOE fallback.

## Missing Implementation

Before evidence download, add:

```text
src/official_sources/sources/borm/artifacts.py
BORM_ARTIFACT_FIELDS
BORMArtifactDownloader
validate_borm_artifact_url
download-source-artifacts --source BORM
download-boe-artifacts --source BORM only if legacy command should remain parallel
BORM-specific download argument validation
tests for scoped BORM artifact downloads
```

Required BORM guardrails:

```text
explicit --source BORM
explicit --candidate-ids
explicit --types
reject --date for BORM downloads
reject --document-ids unless deliberately supported and tested
reject non-BORM candidates
reject missing official URLs clearly
do not invent URLs
limit candidate IDs for first run
backup before download
DB validate after download
MCP privacy check
```

## Future Command Shape

Only after implementation and tests pass:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source BORM \
  --candidate-ids 151,152,153,154,155,156,157,158,159,161,162,163 \
  --types pdf
```

If an implementation proves BORM HTML contains full legal text:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source BORM \
  --candidate-ids 151,152,153,154,155,156,157,158,159,161,162,163 \
  --types html
```

Do not use:

```text
--types xml
```

unless future BORM metadata contains official per-document XML URLs.

## Expected Max Attempts

For one evidence type:

```text
12 candidates x 1 type = 12 attempts
```

For two evidence types:

```text
12 candidates x 2 types = 24 attempts
```

Recommended first operational cap:

```text
12 attempts
```

## Stop Conditions

Stop before running evidence download if:

```text
--source BORM is not accepted
BORM downloader support is missing or untested
candidate IDs are not explicit
candidate IDs include non-BORM candidates
candidate 160 is included
XML is requested while url_xml remains absent
HTML probe returns only an app shell
PDF download is not explicitly requested when PDF is used
backup fails
DB validation fails
artifact_download_attempts already changed unexpectedly
MCP privacy check shows exposed official/MCP service
```

Stop during/after future download if:

```text
attempts exceed expected max
non-selected candidates are touched
source_candidates.review_status changes
downstream files are written
unexpected artifact types appear
DB validation fails
```

## Next Recommended Task

Because BORM downloader support is missing:

```text
TASK-AUTO-BORM-008B — Enable scoped BORM artifact downloader
```

Scope for that task:

```text
code + tests only
no VPS download
no candidates
no downstream
```

After that, run:

```text
TASK-AUTO-BORM-008 — BORM selected evidence download
```

with one explicit candidate-ID list and one explicitly selected evidence type.

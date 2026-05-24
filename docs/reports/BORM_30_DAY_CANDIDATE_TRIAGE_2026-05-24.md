# BORM 30-Day Candidate Triage

Date: 2026-05-24

Task: `TASK-AUTO-BORM-007`

Scope: metadata-only triage of the 13 BORM candidates created by `TASK-AUTO-BORM-006`.

No artifacts were downloaded. No `source_candidates.review_status` values were changed. No downstream project was touched. No approval or publication action was taken.

## Inputs

Reports:

```text
docs/reports/BORM_30_DAY_CANDIDATE_BATCH_2026-05-23.md
docs/reports/NEXT_OPERATIONS_SYNTHESIS_2026-05-24.md
```

Candidates reviewed:

```text
151,152,153,154,155,156,157,158,159,160,161,162,163
```

## VPS/DB Validation

DB validation before and after review:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

Safety counters after review:

```text
source_candidates_total=163
selected_candidates=13
review_status_distribution=human_review_required:13
artifact_download_attempts=482
artifact_bytes=28857411
artifact_size=30M
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching exposed official/MCP/python/uvicorn/fastmcp listener observed
```

## Triage Distribution

```text
candidates_reviewed=13
likely_relevant=9
unclear=3
out_of_scope=1
false_positive=0
selected_for_future_evidence=12
```

Selected for future scoped evidence:

```text
151,152,153,154,155,156,157,158,159,161,162,163
```

Not selected:

```text
160
```

## Candidate Review

| candidate_id | official_identifier | date | metadata classification | evidence action | reason |
| ---: | --- | --- | --- | --- | --- |
| 151 | `BORM:A-140526-2138` | 2026-05-14 | likely_relevant | download_xml_or_html | Youth Eurodisea/practices aid signal; direct youth mobility/employment-training fit. |
| 152 | `BORM:A-130526-2110` | 2026-05-13 | likely_relevant | download_xml_or_html | Fortuna complementary aid for university students/Erasmus mobility. |
| 153 | `BORM:A-130526-2111` | 2026-05-13 | likely_relevant | download_xml_or_html | Textbook and school-material aid; strong EduAyudas fit. |
| 154 | `BORM:A-120526-2086` | 2026-05-12 | likely_relevant | download_xml_or_html | Municipal transport aid for university students. |
| 155 | `BORM:A-110526-2055` | 2026-05-11 | unclear | download_xml_or_html | Third-sector grants for employability of vulnerable youth; may be indirect entity funding. |
| 156 | `BORM:A-080526-2009` | 2026-05-08 | likely_relevant | download_xml_or_html | Erasmus+ practices economic aid for students. |
| 157 | `BORM:A-080526-2010` | 2026-05-08 | likely_relevant | download_xml_or_html | Santander study/economic aid for university students. |
| 158 | `BORM:A-080526-2011` | 2026-05-08 | likely_relevant | download_xml_or_html | Economic aid for master's students. |
| 159 | `BORM:A-080526-2012` | 2026-05-08 | unclear | download_xml_or_html | Campus Rural practices for students; metadata does not confirm economic aid. |
| 160 | `BORM:A-240426-1793` | 2026-04-24 | out_of_scope | do_not_download | Administrative authorization for use of a youth center by entities; no direct aid signal. |
| 161 | `BORM:A-230426-1782` | 2026-04-23 | unclear | download_xml_or_html | Disability/employment integration grant; evidence should confirm beneficiary and directness. |
| 162 | `BORM:A-210426-1745` | 2026-04-21 | likely_relevant | download_xml_or_html | Youth compensation grants/scholarships; strong person-facing signal. |
| 163 | `BORM:A-210426-1746` | 2026-04-21 | likely_relevant | download_xml_or_html | Youth international mobility aid; strong person-facing signal. |

## Evidence Notes

BORM metadata currently preserves official HTML and PDF URLs; XML URLs are absent in the candidate metadata reviewed.

Preferred future evidence path:

```text
HTML first if the BORM downloader can fetch official HTML content reliably.
PDF only if HTML is unavailable, insufficient, or does not contain reviewable legal text.
```

No evidence download should be attempted before confirming scoped BORM artifact downloader behavior and candidate-ID-only safeguards.

## Likely Relevant Examples

Strongest likely relevant candidates:

```text
153 - textbook/material escolar aid
157 - study/economic aid for university students
162 - youth compensation grants/scholarships
163 - youth international mobility aid
```

Other likely relevant candidates:

```text
151,152,154,156,158
```

## Unclear Examples

```text
155 - entity grants for vulnerable youth employability programs; may not be direct/person-facing.
159 - Campus Rural practices; metadata does not confirm economic benefit.
161 - disability/employment integration grant; direct beneficiary and downstream fit need evidence.
```

## Out Of Scope

```text
160 - administrative authorization for youth-center use by entities; do not download evidence.
```

## False Positives

No clear false positives were found in metadata-only triage. Candidate `160` is better classified as out of scope rather than a matcher false positive because it matched a youth/family administrative context but is not an aid.

## Noise Observations

- Some BORM candidates are still entity/intermediary grants rather than direct citizen aids.
- Some university/practices records need evidence to confirm whether there is an economic component.
- Metadata-only triage is enough to select evidence candidates, but not enough for downstream routing.
- BORM HTML/PDF evidence support should remain scoped to explicit candidate IDs.

## Status Verification

```text
source_candidates.review_status=human_review_required for all 13 reviewed candidates
source_candidates_total unchanged during triage
artifact_download_attempts unchanged
artifact directory unchanged
DB valid
MCP privacy OK
```

## Next Recommended Task

```text
TASK-AUTO-BORM-008-PREP — BORM selected evidence download preflight
```

Recommended scope:

```text
candidate_ids=151,152,153,154,155,156,157,158,159,161,162,163
metadata-selected only
prefer HTML if supported
PDF only if HTML is unavailable or insufficient
no date-level downloads
no downstream writes
no review_status changes
```

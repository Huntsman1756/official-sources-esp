# BOJA Pilot Closure - 2026-05-20

## Executive Summary

The BOJA pilot is closed at the reviewed-evidence decision stage.

BOJA can be integrated into `official-sources` as a metadata-first autonomous/statutory territory
source. The 30-day pilot produced usable candidates, but the source required source-specific
candidate profile refinement and detail-endpoint URL enrichment before evidence download was safe.

No downstream project was touched. Nothing was approved or published.

## Pilot Chain Validated

Validated BOJA chain:

```text
BOJA metadata
-> official_documents
-> source_candidates
-> triage
-> URL enrichment
-> scoped PDF download
-> PDF evidence review
-> candidate_evidence_reviews
-> no downstream import
-> no approval
-> no publication
```

## What Was Validated

The pilot validated:

- BOJA official OpenAPI discovery.
- Metadata ingestion by date through the official API.
- Pagination completeness guard based on `total_hits`.
- No-publication classification for observed BOJA empty-date behavior.
- Controlled 30-day metadata backfill.
- BOJA-specific candidate profile `boja-ayudas`.
- Limited candidate creation with `human_review_required` status.
- Metadata-only candidate triage.
- Evidence URL enrichment through the official detail endpoint.
- Scoped PDF download by explicit candidate IDs.
- PDF evidence review.
- Operational evidence decisions applied to `candidate_evidence_reviews`.

## Final Pilot Metrics

| Metric | Value |
| --- | ---: |
| BOJA window | 2026-04-21 to 2026-05-20 |
| 30-day BOJA documents | 1500 |
| BOJA source candidates created | 25 |
| Candidates selected for evidence | 10 |
| PDFs downloaded | 10 |
| Accepted for downstream pilot | 4 |
| Out of scope after evidence review | 6 |
| Needs more evidence | 0 |
| False positives after evidence review | 0 |
| Downstream writes | 0 |
| Approvals | 0 |
| Publications | 0 |

Accepted for downstream pilot:

```text
77, 78, 80, 86
```

Suggested routing:

```text
EduAyudas: 77, 78, 80, 86
```

Out of scope after evidence review:

```text
79, 81, 82, 87, 93, 98
```

## Key Technical Findings

### Official API Shape

BOJA's `search_pagination` endpoint is useful for metadata ingestion, date filtering, and stable
document identifiers, but the stored search response did not provide enough evidence URL data for
PDF download.

The official detail endpoint is required for scoped evidence URL enrichment:

```text
GET /api/v0/boja/{bid}
```

The detail response provided PDF metadata such as `pdf[].publicUrl`, `pdf[].pathPdf`, and `hashPdf`.

### Pagination

BOJA pagination must use `total_hits` as a completeness target. Page 0 alone is not safe for
backfills. The implemented guard fetches pages until the expected total is reached and fails rather
than silently accepting incomplete pagination.

### No-Publication Behavior

BOJA no-publication behavior is source-specific. The exact observed response:

```json
{"status":400,"message":"Bad request"}
```

for a valid date query is treated as `no_publication`. Other 400 bodies, 404, 5xx, malformed
payloads, and incomplete pagination remain failures.

### Candidate Profile

The BOE `la-ayuda` profile over-matched BOJA metadata:

```text
BOJA with la-ayuda: 217/1500 = 14.47%
BOJA with boja-ayudas: 36/1500 = 2.40%
reduction=83.41%
```

BOJA needs source-specific deterministic matching rules. Broad subsidy terms in autonomous
metadata generate too much noise without stricter co-occurrence and exclusion handling.

### Evidence URLs

BOJA evidence URL enrichment required the detail endpoint. The downloader correctly skipped PDFs
when `url_pdf` was missing and did not infer URLs.

PDF URL canonicalization was also required:

```text
juntadeandalucia.es -> www.juntadeandalucia.es
```

The accepted official PDF URLs are now persisted in canonical form before scoped download.

### CLI Naming Debt

The current candidate command still uses the name:

```text
find-boe-candidates --source BOJA
```

It works with source filtering, but the name is semantically awkward. A future
`find-source-candidates` alias would reduce operator confusion.

## Safety Guarantees Preserved

The BOJA pilot preserved the project safety model:

- No downstream writes.
- No approvals.
- No publication.
- All `source_candidates` remain `human_review_required`.
- MCP remained private; no public listener was observed.
- PDFs were downloaded only by explicit selected candidate IDs.
- No broad PDF download was run.
- No BOJA candidate extraction occurred before metadata profile refinement.
- No BOJA downstream import occurred before evidence review decisions were applied.

## Known Limitations

- BOJA HTML/XML evidence is not implemented.
- Only PDF evidence has been validated for selected BOJA candidates.
- BOJA accepted evidence has not been exported or imported into EduAyudas.
- BOJA date ingestion was performed through one-date commands and shell loops; no BOJA range command
  exists yet.
- A historical failed ingestion run remains for 2026-04-25, although the current date status was
  corrected by the no-publication hardening task.
- There is no generic `find-source-candidates` alias yet.
- There is no production downstream rollout.
- No other autonomous/statutory territory adapter has been implemented.
- Hashes are integrity signals only; electronic signature validation is not implemented.

## Strategic Decision

Recommended decision:

```text
Do not import BOJA evidence into EduAyudas immediately.
```

Rationale:

- BOJA is now validated as a metadata-first autonomous source, but the downstream onboarding pattern
  is still being handled one project at a time.
- The four accepted BOJA candidates may be useful for EduAyudas, but they should enter downstream
  only through a documented, reusable onboarding process.
- BOE, EduAyudas, and BOJA have now exposed the same platform need: a standard contract for how
  downstream projects consume `official-sources` evidence safely.

Alternative options considered:

| Option | Decision |
| --- | --- |
| Export BOJA accepted evidence for EduAyudas staging | Defer until downstream onboarding is formalized. |
| Pause BOJA downstream and audit DOGV/BOCM next | Reasonable later, but not the highest-leverage next step. |
| Add `find-source-candidates` alias and generic source-profile cleanup | Useful cleanup, but not strategic enough to be next. |
| BOJA 3-month metadata backfill | Defer until downstream value and review capacity are clearer. |

## Recommended Next Task

Recommended next task:

```text
TASK-PLATFORM-001 - Downstream onboarding kit for official-sources
```

Scope:

- define a reusable downstream evidence contract and checklist;
- document export/import responsibilities;
- define local/dev versus production-safe import modes;
- define staging review expectations for projects such as EduAyudas and future `la-ayuda`;
- avoid repeating downstream decisions separately for BOE, BOJA, and future autonomous sources.

After the platform kit exists, reasonable next choices are:

```text
TASK-AUTO-011 - Export BOJA accepted evidence for EduAyudas staging
TASK-AUTO-BOCM-001 - BOCM source audit or MVP research
TASK-LAAYUDA-FOUNDATION - add evidence/candidate staging model
```

Do not approve, publish, or write downstream automatically from this closure report.

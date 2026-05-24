# Cross-Project Integration Map

Date: 2026-05-24

Task: `TASK-SOURCE-PLATFORM-001`

This document defines the cross-project boundary for `official-sources`.

The decision:

```text
official-sources = upstream official-source ingestion and evidence platform
downstream projects = staging + review + product decisions
```

`official-sources` must remain a common platform. It must not become the backend for a single
downstream product, including `oposiciones2.0`.

## Platform Identity

`official-sources` is an upstream official-source ingestion and evidence platform.

It may provide:

```text
official metadata
source snapshots
hashes/integrity
citations
artifact availability
candidate/evidence review records
downstream-ready exports
alert-grade dry-run/export feeds
```

It must not become:

```text
product backend
notification engine
public page publisher
oposiciones process manager
benefit/aid CMS
tax advice engine
```

## Two-Track Model

### Evidence-Grade

Evidence-grade is used for:

```text
legal/evidence-backed downstream workflows
human review
publication-safe exports
auditable evidence
```

Characteristics:

```text
hashes
citation
integrity
artifacts when needed
manual review
candidate_evidence_reviews
downstream export only after review
```

Evidence-grade records can support downstream products, but they are not product decisions.
Downstream projects remain responsible for their own staging, review, publication gates, and
domain interpretation.

### Alert-Grade

Alert-grade is used for:

```text
fast monitoring
oposiciones/public employment alerts
metadata-first triage
product review queues
```

Characteristics:

```text
official_url required
confidence
alert_type
alert_scope
dedupe_key
no artifact required by default
no source_candidate by default
no automatic promotion
```

Rule:

```text
alert-grade can request evidence-grade review,
but can never auto-promote to evidence-grade or downstream publication.
```

Alert-grade output is a monitoring/export contract. It can feed product review queues, but it is
not verified evidence and it must not be stored as `source_candidates` by default.

## Project Map

| Project | Track | Consumer role | Current status | Existing integration | Missing pieces | What `official-sources` should provide | What `official-sources` must not do | Next recommended task |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `oposiciones2.0` | Alert-grade | Product-specific alert/review pipeline | Strict alerts exported from `official-sources`; 200 imported into local/staging `ImportedSourceAlert`; internal review page exists; promotion planner preview exists; no process creation, events, matches, or notifications. | Alert-grade JSON/JSONL export contract from stored metadata and strict alert sample. | Accepted platform boundary; explicit draft-process design inside `oposiciones2.0`; storage/promotion rules owned by the product. | Alert-grade JSON/JSONL exports, source metadata, official URLs, dedupe keys, source registry, optional evidence-grade promotion inputs later. | Create `PublicEmploymentProcess`, `ProcessEvent`, `ProcessMatch`, notifications, user subscriptions, or product ranking. | Pause new write actions until this platform map is accepted; then continue only with explicit draft-process design inside `oposiciones2.0`. |
| `EduAyudas` | Evidence-grade | Aid/scholarship official evidence consumer | `official_source_evidence` exists; `source_candidates` conversion exists; local/dev fallback exists; no automatic `aid_program` creation or publication. | BOE/BOJA-style evidence staging and downstream review pattern. | Clean product state before more imports; production-safe import path; small preview/import batches. | Reviewed evidence exports, official identifiers, citations, integrity, artifact availability, manual decisions. | Create `aid_programs` directly, publish aids, decide eligibility, or bypass EduAyudas review/admin flow. | Resume only after current EduAyudas product fixes are clean; then preview/import small batches, not bulk. |
| `la-ayuda` | Evidence-grade | File-based/Astro aid staging consumer | Evidence staging exists; candidate staging exists; BOE candidate 69 flow validated to draft/internal review; DOGV candidate 117 evidence staging exists; no public page unless draft/review process explicitly allows. | Downstream-ready evidence JSON preview/write pattern and local staging gates. | Continue explicit staging/candidate/draft steps; avoid public route creation without review approval. | Downstream-ready evidence JSON, citation/integrity, artifact availability, routing suggestions. | Create benefit markdown directly, publish pages, invent missing fields, or skip local preview/staging gates. | Continue only with explicit staging/candidate/draft steps. |
| `renta-verificable` | Evidence-grade, secondary | Fiscal/legal reference consumer | Not materially integrated with `official-sources`; BOE may be useful for legal/versioned evidence; AEAT remains primary for fiscal guidance. | No material integration. | Exact source-needs audit before any integration; AEAT-first contract. | BOE/legal reference evidence, versioned official source metadata, possibly autonomous legal references. | Replace AEAT, generate tax conclusions alone, act as fiscal product backend, or treat alert-grade as tax evidence. | Audit exact `renta-verificable` source needs before integration. |
| `subvenciones` / future grants project | Evidence-grade | Grants registry and subsidy review consumer | BDNS adapter MVP exists for `convocatorias` only; `concesiones` deferred; no downstream bulk import. | BDNS metadata-only source family, raw JSON hash, official identifiers, controlled profile design. | Grants-specific staging model; privacy/retention policy before concessions; controlled dry-runs before imports. | BDNS convocatoria metadata, official identifiers, raw JSON hash, citation/integrity where applicable, controlled exports. | Treat concessions casually, ignore privacy/retention, or bulk-publish grants without review. | Design grants-specific staging/review before any bulk import; keep concessions deferred until privacy review. |

## Project-Specific Boundaries

### `oposiciones2.0`

Track:

```text
alert-grade
```

Consumer role:

```text
product-specific alert/review pipeline
```

Current status:

```text
strict alerts exported from official-sources
200 imported into local/staging ImportedSourceAlert
internal review page exists
promotion planner preview exists
no process creation yet
no events
no matches
no notifications
```

`official-sources` should provide:

```text
alert-grade JSON/JSONL exports
source metadata
official URLs
dedupe keys
source registry
optional evidence-grade promotion inputs later
```

`official-sources` must not provide:

```text
PublicEmploymentProcess
ProcessEvent
ProcessMatch
notifications
user subscriptions
product ranking
```

Next recommended task:

```text
pause new write actions until platform map is accepted
then continue with explicit draft-process design only inside oposiciones2.0
```

### `EduAyudas`

Track:

```text
evidence-grade
```

Consumer role:

```text
aid/scholarship official evidence consumer
```

Current status:

```text
official_source_evidence exists
source_candidates conversion exists
local/dev fallback exists
no automatic aid_program creation
no automatic publication
```

`official-sources` should provide:

```text
reviewed evidence exports
official identifiers
citations
integrity
artifact availability
manual decisions
```

`official-sources` must not:

```text
create aid_programs directly
publish aids
decide eligibility
bypass EduAyudas review/admin flow
```

Next recommended task:

```text
resume only after current EduAyudas product fixes are clean
then preview/import small batches, not bulk
```

### `la-ayuda`

Track:

```text
evidence-grade
```

Consumer role:

```text
file-based/Astro aid staging consumer
```

Current status:

```text
evidence staging exists
candidate staging exists
BOE candidate 69 flow validated to draft/internal review
DOGV candidate 117 evidence staging exists
no public page unless draft/review process explicitly allows
```

`official-sources` should provide:

```text
downstream-ready evidence JSON
citation/integrity
artifact availability
routing suggestions
```

`official-sources` must not:

```text
create benefit markdown directly
publish pages
invent missing fields
skip local preview/staging gates
```

Next recommended task:

```text
continue only with explicit staging/candidate/draft steps
```

### `renta-verificable`

Track:

```text
evidence-grade, but secondary
primary source = AEAT
```

Current status:

```text
not materially integrated with official-sources
BOE may be useful for legal/versioned evidence
AEAT remains primary for fiscal guidance
```

`official-sources` should provide:

```text
BOE/legal reference evidence
versioned official source metadata
possibly autonomous legal references
```

`official-sources` must not:

```text
replace AEAT
generate tax conclusions alone
act as fiscal product backend
treat alert-grade as tax evidence
```

Next recommended task:

```text
audit exact renta-verificable source needs before integration
```

### BDNS / `subvenciones`

BDNS role:

```text
BDNS = grants_registry / primary grants source
```

Current status:

```text
BDNS adapter MVP exists
convocatorias only
concesiones deferred
no downstream bulk import
```

`official-sources` should provide:

```text
BDNS convocatoria metadata
official identifiers
raw JSON hash
citation/integrity where applicable
controlled exports
```

`official-sources` must not:

```text
treat concessions casually
ignore privacy/retention
bulk-publish grants without review
```

## Operational Boundaries

Hard rules:

```text
VPS/DB operations: one agent only
downstream writes: project-specific only
artifact downloads: scoped by candidate/document only
backfills: one source at a time
candidate creation: limited batches
alert-grade exports: read-only/export-only until product storage is approved
```

Additional rules:

- Downstream repos must not be modified from platform tasks.
- Dirty downstream worktrees must be left untouched.
- Artifact downloads must use source-specific scoped commands and must not infer missing URLs.
- Broad backfills require a separate task, backup plan, run report, and source-specific scope.
- Candidate creation is a review queue operation, not a publication operation.
- Alert-grade samples are not publication-safe evidence.

## Integration Contracts

| Contract | Track | Current consumers | Purpose | Boundary |
| --- | --- | --- | --- | --- |
| `evidence_export_json` | Evidence-grade | `EduAyudas`, `la-ayuda`, future grants workflows | Reviewed official evidence with citation, integrity, artifact availability, and manual decision metadata. | Downstream staging only; no direct product publication. |
| `alert_grade_jsonl` | Alert-grade | `oposiciones2.0` | Fast metadata-first alert feed with official URL, alert type/scope, confidence, and dedupe key. | Export/review only; no `source_candidates` by default and no automatic evidence promotion. |
| Downstream evidence staging | Evidence-grade | `EduAyudas`, `la-ayuda`, future grants workflows | Local downstream storage of official evidence before candidates or drafts. | Owned by downstream projects; import must preserve citation and integrity. |
| Candidate staging | Evidence-grade | `EduAyudas`, `la-ayuda`, future grants workflows | Downstream-specific `pending_review` candidates derived from evidence. | Owned by downstream projects; not created directly by `official-sources`. |
| Review decision reports | Evidence-grade / operational | Platform operators and downstream reviewers | Auditable record of evidence review, artifact status, and manual decisions. | Reports are decision inputs, not downstream publication commands. |

Project consumption summary:

| Project | Consumed contracts |
| --- | --- |
| `oposiciones2.0` | `alert_grade_jsonl`; optional future evidence-grade promotion inputs after explicit request. |
| `EduAyudas` | `evidence_export_json`; downstream evidence staging; candidate staging; review decision reports. |
| `la-ayuda` | `evidence_export_json`; file-based preview/import; downstream evidence staging; candidate/draft staging. |
| `renta-verificable` | Future evidence/reference contract after source-needs audit; no alert-grade tax evidence. |
| `subvenciones` / grants | Future BDNS `evidence_export_json` or grants-specific export; candidate staging after grants foundation. |

## Anti-Patterns

Explicitly rejected:

```text
official-sources creates product records directly
alert-grade stored as source_candidates
oposiciones logic pushed into official-sources core
bulk imports without preview
artifact downloads without scope
downstream publication from official-sources
automatic promotion alert-grade -> evidence-grade
```

Also rejected:

- Treating `likely_relevant`, `accept_for_downstream_pilot`, or `confidence=high` as approval.
- Reusing BOE source rules for autonomous, provincial, BDNS, fiscal, or grants-specific evidence
  without source-specific validation.
- Turning deterministic prefilter scores into ranking, eligibility, or publication decisions.
- Allowing alert-grade output to bypass human/product review.

## Next Recommended Tasks

1. Review and accept this cross-project map.
2. Resume one source operation at a time in `official-sources`.
3. For `oposiciones2.0`, continue only with design/preview for draft process creation.
4. For `EduAyudas`, wait until current dirty state/product fixes are clean.
5. For `la-ayuda`, continue staging-first only.
6. For `renta-verificable`, run a source-needs audit before integration.

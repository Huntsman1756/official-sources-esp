# Cross-Project Integration Map Report

Date: 2026-05-24

Task: `TASK-SOURCE-PLATFORM-001`

## Summary Decision

`official-sources` remains the common upstream official-source ingestion and evidence platform.

The boundary is:

```text
official-sources = official metadata, source snapshots, hashes, citations, artifacts, review records, and export contracts
downstream projects = staging, human/product review, product records, publication, notifications, and domain decisions
```

The recent `oposiciones2.0` alert-grade work is useful, but it must stay a consumer-specific
integration path. `official-sources` must not become an `oposiciones2.0` product backend.

## Project Table

| Project | Track | Consumer role | Current status | Existing integration | Missing pieces | What `official-sources` should provide | What `official-sources` must not do | Next recommended task |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `oposiciones2.0` | Alert-grade | Product-specific alert/review pipeline | Strict alerts exported; 200 imported into local/staging `ImportedSourceAlert`; internal review page exists; promotion planner preview exists; no process creation, events, matches, or notifications. | Alert-grade JSON/JSONL export and strict sample. | Accepted boundary; product-owned draft-process design. | Alert-grade JSON/JSONL exports, source metadata, official URLs, dedupe keys, source registry, optional evidence-grade promotion inputs later. | Create `PublicEmploymentProcess`, `ProcessEvent`, `ProcessMatch`, notifications, user subscriptions, or product ranking. | Pause new write actions until this map is reviewed; then continue only with explicit draft-process design in `oposiciones2.0`. |
| `EduAyudas` | Evidence-grade | Aid/scholarship official evidence consumer | `official_source_evidence` exists; `source_candidates` conversion exists; local/dev fallback exists; no automatic `aid_program` creation or publication. | Evidence staging and review pattern. | Clean product state; production-safe import path; small preview/import batches. | Reviewed evidence exports, official identifiers, citations, integrity, artifact availability, manual decisions. | Create `aid_programs`, publish aids, decide eligibility, or bypass review/admin flow. | Resume only after current product fixes are clean; then preview/import small batches. |
| `la-ayuda` | Evidence-grade | File-based/Astro aid staging consumer | Evidence staging exists; candidate staging exists; BOE candidate 69 validated to draft/internal review; DOGV candidate 117 evidence staging exists; no public page unless draft/review allows. | Downstream-ready evidence JSON preview/write pattern. | Continue staging/candidate/draft gates; avoid direct public route creation. | Downstream-ready evidence JSON, citation/integrity, artifact availability, routing suggestions. | Create benefit markdown directly, publish pages, invent fields, or skip preview/staging gates. | Continue only with explicit staging/candidate/draft steps. |
| `renta-verificable` | Evidence-grade, secondary | Fiscal/legal reference consumer | Not materially integrated; BOE may help with legal/versioned evidence; AEAT remains primary for fiscal guidance. | None material. | Source-needs audit and AEAT-first contract. | BOE/legal reference evidence, versioned official source metadata, possible autonomous legal references. | Replace AEAT, generate tax conclusions alone, act as fiscal backend, or treat alert-grade as tax evidence. | Audit exact source needs before integration. |
| `subvenciones` / future grants project | Evidence-grade | Grants registry and subsidy review consumer | BDNS adapter MVP exists for `convocatorias`; `concesiones` deferred; no downstream bulk import. | BDNS metadata-only adapter and profile design. | Grants-specific staging; privacy/retention policy before concessions. | BDNS convocatoria metadata, official identifiers, raw JSON hash, citation/integrity where applicable, controlled exports. | Treat concessions casually, ignore privacy/retention, or bulk-publish grants without review. | Design grants staging/review before bulk import; keep concessions deferred. |

## Boundaries

### Platform role

`official-sources` may provide:

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

`official-sources` must not become:

```text
product backend
notification engine
public page publisher
oposiciones process manager
benefit/aid CMS
tax advice engine
```

### Evidence-grade vs alert-grade

Evidence-grade supports legal/evidence-backed workflows:

```text
hashes
citation
integrity
artifacts when needed
manual review
candidate_evidence_reviews
downstream export only after review
```

Alert-grade supports fast monitoring:

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

Task-specific compliance:

```text
code changes: none
DB operations: none
VPS operations: none
downstream repos touched: none
backfills/imports/exports run: none
source adapters modified: none
```

## Risks

| Risk | Impact | Control |
| --- | --- | --- |
| `official-sources` becomes `oposiciones2.0` backend | Common platform boundary erodes and product logic enters source core. | Keep `PublicEmploymentProcess`, events, matches, notifications, subscriptions, and ranking in `oposiciones2.0`. |
| Alert-grade is treated as evidence | User-facing or publication claims may use unverified metadata. | Keep alert-grade separate from `source_candidates`; require explicit evidence-grade request and human review. |
| Bulk imports skip preview | Downstream products may publish or stage bad records. | Require preview/staging gates and small batches. |
| Artifact downloads expand without scope | Unbounded source load and noisy evidence state. | Candidate/document-scoped downloads only. |
| BDNS concessions are treated casually | Privacy/retention and beneficiary-data risk. | Keep concessions deferred until privacy-aware design. |
| Fiscal workflows overtrust BOE evidence | Tax guidance may become inaccurate or incomplete. | Keep AEAT primary for `renta-verificable`; audit needs first. |

## Integration Contracts

| Contract | Track | Projects | Boundary |
| --- | --- | --- | --- |
| `evidence_export_json` | Evidence-grade | `EduAyudas`, `la-ayuda`, future grants workflows | Reviewed evidence for staging only; no direct publication. |
| `alert_grade_jsonl` | Alert-grade | `oposiciones2.0` | Monitoring/review feed only; no automatic `source_candidates` or publication. |
| Downstream evidence staging | Evidence-grade | `EduAyudas`, `la-ayuda`, future grants workflows | Owned by downstream; must preserve citation/integrity. |
| Candidate staging | Evidence-grade | `EduAyudas`, `la-ayuda`, future grants workflows | Downstream-specific `pending_review`; not direct product publication. |
| Review decision reports | Operational evidence | Platform and downstream reviewers | Audit input; not a downstream write command. |

## Anti-Patterns Rejected

```text
official-sources creates product records directly
alert-grade stored as source_candidates
oposiciones logic pushed into official-sources core
bulk imports without preview
artifact downloads without scope
downstream publication from official-sources
automatic promotion alert-grade -> evidence-grade
```

## Next Recommended Tasks

1. Review and accept the cross-project map.
2. Resume one source operation at a time in `official-sources`.
3. For `oposiciones2.0`, continue only with design/preview for draft process creation.
4. For `EduAyudas`, wait until current dirty state/product fixes are clean.
5. For `la-ayuda`, continue staging-first only.
6. For `renta-verificable`, run a source-needs audit before integration.

## Pause Recommendation

Pause new `oposiciones2.0` write actions until this map is reviewed and accepted.

The next `oposiciones2.0` work should be product-local design/preview for draft process creation,
not additional platform writes, source adapter changes, or promotion logic in `official-sources`.

## Validation

Docs-only validation required:

```bash
git diff --check
```

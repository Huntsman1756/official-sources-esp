# Downstream Onboarding

This guide explains how downstream projects can safely consume `official-sources` evidence.

It generalizes the BOE-to-EduAyudas pilot and the BOJA pilot into a reusable onboarding model for
future projects.

## What `official-sources` Is

`official-sources` is an official evidence platform.

It provides:

- official source metadata;
- official document identifiers;
- official URLs;
- citation metadata;
- integrity metadata;
- controlled artifact availability;
- candidate prefilter metadata;
- evidence review metadata;
- read-only retrieval surfaces for trusted local consumers.

It is designed to preserve source provenance and review safety while downstream projects make their
own domain decisions.

## What `official-sources` Is Not

`official-sources` is not:

- a publication system;
- a downstream CMS;
- a legal, fiscal, procurement, or eligibility decision engine;
- a generic web scraper;
- a public API by default;
- an approval workflow;
- a replacement for downstream human review;
- a RAG or semantic search system;
- a source of final user-facing descriptions.

`official-sources` must not publish, approve, or directly write public downstream records.

## Required Downstream Readiness

A downstream project must have a safe staging model before consuming `official-sources`.

Minimum required capabilities:

```text
candidate/evidence staging
pending_review workflow
source_url storage
official_identifier storage
citation_json storage
source_snapshot_hash
content_sha256
hashes_match
has_integrity_warning
integrity_warning_reason
artifact availability
manual review state
publication gate
admin/staff review surface
```

If a downstream project does not have these, the first task is foundation, not integration.

## Evidence Contract

Downstream projects should consume the contract documented in:

```text
docs/DOWNSTREAM_CONTRACT.md
docs/examples/downstream_evidence_contract.example.json
```

The contract preserves:

- `source_code`;
- `resource_type`;
- `official_identifier`;
- `official_url`;
- citation metadata;
- integrity metadata;
- artifact availability;
- optional `official_sources_candidate` review metadata.

Do not include raw legal text by default in downstream evidence exports. Raw text should be a
separate explicit retrieval path and must remain review-gated.

## Candidate And Staging Model

Downstream projects should store official evidence separately from downstream publication records.

Recommended minimum staging tables or equivalent models:

| Model | Purpose |
| --- | --- |
| Evidence staging | Stores imported official evidence and integrity/citation metadata. |
| Source candidates | Stores downstream-specific candidate records with `pending_review` status. |
| Draft records | Stores domain-specific drafts after explicit human decision. |
| Publication records | Stores public records only after downstream review and publication gates. |

Recommended status flow:

```text
official evidence
-> downstream evidence staging
-> source_candidate pending_review
-> optional draft
-> downstream human approval
-> publication
```

`official-sources` should not skip directly to draft or publication.

## Review Workflow Requirements

The downstream review surface must show:

- official title;
- official source code;
- official identifier;
- official URL;
- publication date;
- citation metadata;
- artifact availability;
- integrity hash status;
- integrity warnings;
- evidence review decision from `official-sources` when present;
- downstream-specific reviewer decision.

Reviewers must be able to reject, defer, or request more evidence without changing official-source
state.

## Publication Safety Rules

Required rules:

- Imported evidence must default to `pending_review`.
- Import must never publish records.
- `accept_for_downstream_pilot` is not approval.
- `likely_relevant` is not approval.
- PDF availability is not verification.
- Missing PDF is not invalidation.
- Integrity warnings must block automatic publication.
- Downstream publication must remain outside `official-sources`.

## Integrity And Citation Requirements

Downstream projects must store:

- `official_identifier`;
- `official_url`;
- `citation_json`;
- `source_snapshot_hash`;
- `content_sha256`;
- `hashes_match`;
- `has_integrity_warning`;
- `integrity_warning_reason`;
- `last_integrity_check_at`;
- `content_changed_at`.

Hashes are integrity signals. They are not electronic signature validation unless a source-specific
signature validation path exists and is tested.

## Cache-Miss Behavior

`official-sources` can return structured cache misses for read-only consumers.

A cache miss means evidence is not present locally. It must not trigger live fetching, candidate
creation, approval, or publication automatically.

Required downstream behavior:

- show the cache miss as unavailable evidence;
- schedule a controlled ingestion or artifact task if needed;
- keep downstream candidates blocked or pending until evidence exists.

## Supported Integration Patterns

### Pattern A - Manual Export/Import

Safest and slowest.

`official-sources` exports reviewed evidence JSON files. A downstream operator imports them into an
ignored local or staging folder and runs a preview/import command.

Use when:

- onboarding a new downstream;
- validating a new source family;
- production write paths are not ready.

### Pattern B - Preview-Only Import

The downstream project validates the evidence JSON without writing data.

Use when:

- testing schema compatibility;
- checking integrity/citation fields;
- validating that no raw legal text or local paths leak.

### Pattern C - Evidence Staging Write

The downstream project writes only to its evidence staging table.

Use when:

- evidence contract is validated;
- staging table exists;
- source candidates should not be created yet.

### Pattern D - Candidate Creation

The downstream project creates source candidates only as `pending_review`.

Use when:

- evidence staging rows are visible in an admin review surface;
- candidate creation is explicit;
- publication gates are tested.

### Pattern E - Draft Creation

The downstream project creates a domain draft only after an explicit human decision and with a
structured evidence link.

Publication must remain downstream-owned and outside `official-sources`.

## Anti-Patterns

Forbidden or dangerous patterns:

- `official-sources` writes directly to public tables.
- Evidence import creates published records.
- `likely_relevant` means approved.
- `accept_for_downstream_pilot` means approved.
- PDF availability means verified.
- Missing PDF means invalid.
- Generic `acceptCandidate` bypasses official-source review.
- MCP is exposed publicly.
- Downstream stores only free-text source notes.
- Raw legal text is shown publicly by default.
- Integrity warnings are ignored.
- Candidate prefilter score is used as a ranking or approval score.
- Downstream mutates `official-sources` candidate status to fit its own workflow.

## Project-Specific Notes

### EduAyudas

EduAyudas has a validated local/dev path:

```text
official_source_evidence
-> source_candidates pending_review
-> selected aid_program drafts
-> structured evidence links
-> admin review
-> no publication
```

Production rollout still needs a remote-safe import path. The local/dev SQL workaround used during
rehearsal is not a production pattern.

### la-ayuda

`la-ayuda` has reserved evidence, but it lacks a robust candidate/evidence staging foundation.

First task should be foundation:

```text
evidence staging
source candidates
pending_review workflow
admin/staff review surface
publication gate
```

Do not import evidence until that foundation exists.

### oposiciones2.0

Likely source families:

- BOE;
- autonomous/statutory territory bulletins;
- provincial/local bulletins for some calls.

This project should implement foundation first because candidate semantics, deadlines, territorial
scope, and review rules will differ from aid/subsidy projects.

### renta-verificable

This is a high-risk fiscal domain. BOE evidence alone is not enough.

Likely needs:

- AEAT or other tax authority sources;
- BOE legal and consolidated legislation evidence;
- explicit legal/fiscal review gates;
- strong warning and freshness semantics.

Do not use `official-sources` as a tax decision engine.

### subvenciones

BDNS is likely the primary source family. BOE and BOJA evidence can provide supporting official
context, but they should not replace a BDNS-first model.

Required foundation:

- grant-specific staging;
- beneficiary/issuer model;
- call versus award/resolution distinction;
- explicit publication and deadline checks.

### contratosabiertos

PLACSP is likely the primary source. `official-sources` may provide contextual references such as
official bulletins, legal notices, or procurement-related official documents.

Do not model procurement around BOE/BOJA alone.

## Onboarding Checklist

Before integration:

- project profile exists;
- evidence contract fields are stored;
- preview-only import passes;
- staging write is separate from candidate creation;
- candidate creation defaults to `pending_review`;
- admin review surface shows citation and integrity;
- publication gate is separate and tested;
- production write path is explicit and reversible;
- secrets, local paths, raw legal text, and VPS details are not exported.

## Recommended Next Task

Recommended next task after this onboarding kit:

```text
TASK-LAAYUDA-FOUNDATION - add evidence/candidate staging model
```

Reason:

- BOE and BOJA have validated `official-sources` as a reusable evidence platform.
- EduAyudas is already validated in local/dev.
- `la-ayuda` is the next downstream that needs a safe staging foundation before importing reserved
  evidence.

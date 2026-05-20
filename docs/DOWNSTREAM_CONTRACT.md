# Downstream Contract

This document defines how downstream projects consume `official-sources`.

For the operational onboarding guide and examples, see:

```text
docs/DOWNSTREAM_ONBOARDING.md
docs/examples/downstream_evidence_contract.example.json
docs/examples/downstream_profile.example.yaml
```

## Purpose

Downstream projects use `official-sources` to retrieve official evidence, citations,
integrity status, official text, source URLs, and artifact status.

Downstream projects remain responsible for their own domain decisions, candidates, review
workflow, publication workflow, legal or fiscal interpretation, and user-facing content.

## Contract Rules

- `official-sources` is read-only from the perspective of downstream projects.
- `official-sources` does not write into downstream projects.
- Downstream projects must create their own `pending_review` candidates.
- `official-sources` does not approve candidates.
- `official-sources` does not publish anything.
- `official-sources` does not decide eligibility, tax applicability, legal validity, ranking,
  grant amounts, or deadline compliance.
- `official-sources` does not provide legal advice.
- Every downstream use must preserve citation metadata and source URL.
- Every downstream use must preserve integrity metadata where relevant.
- Downstream projects must preserve integrity warnings where relevant.
- Downstream projects must handle missing text, missing artifacts, stale cache, and failed
  downloads explicitly.
- Downstream projects must not treat `official-sources` output as a final legal, fiscal, or
  product decision.
- Keyword candidate prefiltering is title/metadata matching only. It does not parse full
  document content, classify legal meaning, or decide eligibility.
- Prefiltered candidates are false-positive-prone and must remain
  `human_review_required`.
- Candidate prefilter scores, when present, are deterministic and explainable matching signals
  only. They are not risk scores, rankings, recommendations, legal decisions, approval signals,
  or publication decisions.

## Required evidence object

Downstream evidence should preserve this stable shape. Field names may be adapted at the
consumer boundary, but the meaning must not be weakened.

```json
{
  "source_code": "BOE",
  "resource_type": "official_document|consolidated_law|consolidated_law_block",
  "official_identifier": "BOE-A-YYYY-NNNNN",
  "title": "...",
  "publication_date": "YYYY-MM-DD",
  "version_date": "YYYY-MM-DD|null",
  "official_url": "https://www.boe.es/...",
  "citation": {
    "source_code": "BOE",
    "resource_type": "...",
    "official_identifier": "...",
    "title": "...",
    "official_url": "...",
    "publication_date": "...",
    "version_date": null
  },
  "integrity": {
    "source_snapshot_hash": "ingestion-time raw payload hash",
    "content_sha256": "latest-check/current artifact hash",
    "hashes_match": true,
    "last_integrity_check_at": "YYYY-MM-DDTHH:MM:SSZ",
    "content_changed_at": null,
    "has_integrity_warning": false,
    "integrity_warning_reason": null
  },
  "text": {
    "available": true,
    "content_type": "official_legal_text",
    "is_official_text": true,
    "content": "..."
  }
}
```

## Candidate Evidence Metadata

Candidate evidence review metadata is operational review state inside `official-sources`.
It is not a publication workflow and it is not an approval workflow.

Downstream projects can consume evidence metadata, but they must still create and maintain
their own review workflow.

```json
{
  "candidate": {
    "candidate_id": 1,
    "review_status": "human_review_required",
    "evidence_review_status": "evidence_downloaded",
    "evidence_label": "likely_relevant"
  },
  "evidence": {
    "xml_available": true,
    "html_available": true,
    "pdf_available": false,
    "pdf_policy": "on_demand",
    "integrity_warning": false
  }
}
```

Required interpretation:

- `likely_relevant is not approval`.
- `false_positive` is operational review, not a legal conclusion.
- `PDF is on-demand`.
- PDF absence does not mean evidence is invalid.
- PDF presence does not mean candidate is approved.
- `source_candidates.review_status` remains publication-safe and must not be overloaded with
  operational evidence labels.

## Integrity Hash Semantics

`source_snapshot_hash` represents the hash of the raw official source payload at ingestion
time.

`content_sha256` represents the hash observed at the latest integrity check or the latest
stored artifact state, depending on the resource type.

`hashes_match` is a derived boolean intended for downstream projects. Downstream projects
should not compare hash strings manually. They should rely on `hashes_match`,
`content_changed_at`, `has_integrity_warning`, and `integrity_warning_reason`.

When `hashes_match = false` or `content_changed_at` is not null, the downstream project must
preserve the warning and flag the candidate or evidence for human review. This requires re-review, not automatic rejection.

This does not mean automatic rejection. It means the evidence is not silently safe to reuse
without review.

## Optional Fields

Optional fields include `clean_text`, `html_url`, `xml_url`, `pdf_url`, `block_id`,
`block_type`, `block_identifier`, `block_title`, `retrieved_at`, `download_attempt_status`,
`integrity_warning`, `artifact_status`, and `last_seen_at`.

## Never Authoritative Decisions

Downstream projects must not treat these as authoritative decisions from `official-sources`:

- `eligibility`
- `tax_applicability`
- `grant_amount`
- `deadline_compliance`
- `legal_validity_for_case`
- `publication_ready`
- `risk_score`
- `ranking`
- `recommendation`
- `prefilter_score` as an approval or ranking decision

## Integrity Warning Behavior

When `integrity.content_changed_at` is not null, downstream projects must not silently ignore
the signal.

Required behavior:

- Do not treat the evidence as definitively current without review.
- Re-fetch the evidence or flag the candidate for re-review.
- Preserve the integrity warning in the downstream candidate or evidence record.
- Show the warning to the human reviewer or admin.
- Do not automatically reject the candidate solely because content changed.
- Do not automatically approve or publish the candidate while the warning is unresolved.

This is not an automatic rejection rule. It is a signal that human review must be informed of
the detected change. Unresolved integrity warnings must block automatic approval/publication.

## Cache Miss Behavior

Read-only consumers may receive structured cache misses when evidence is not present locally:

```json
{
  "status": "cache_miss",
  "resource_type": "boe_summary",
  "date": "YYYY-MM-DD",
  "recommended_action": "Run controlled BOE ingestion for this date"
}
```

Cache misses do not trigger live fetching, downstream writes, candidate approval, or
publication. Consumers must treat them as a signal to schedule an explicit controlled
ingestion or artifact download step.

## Example downstream flow

1. `la-ayuda` queries `official-sources` for BOE documents or consolidated law blocks.
2. `official-sources` returns official evidence with citation and integrity metadata.
3. `la-ayuda` stores the evidence reference locally.
4. `la-ayuda` creates its own candidate with status `pending_review`.
5. A human or admin reviews and accepts or rejects the candidate.
6. `la-ayuda` publishes only after its own review workflow passes.

No downstream integration is implemented by this repository in TASK-003F.

## Onboarding Requirement

Every new downstream project must have an onboarding profile and a staging/review foundation before
evidence import.

Minimum foundation:

- evidence staging;
- candidate staging with `pending_review`;
- citation and integrity storage;
- admin/staff review surface;
- publication gate separate from import.

Projects without this foundation should start with a foundation task, not an import task.

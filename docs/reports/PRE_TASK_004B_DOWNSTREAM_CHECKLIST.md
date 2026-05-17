# Pre-TASK-004B downstream readiness checklist

This checklist is used before starting a read-only pilot integration from `official-sources`
into `la-ayuda` or `EduAyudas`.

TASK-004B duration depends on downstream readiness. If the downstream project lacks candidate,
evidence, or `pending_review` primitives, the pilot integration must first add those primitives
to the downstream project before consuming `official-sources`.

## Readiness Questions

- Does the downstream project have a candidates/evidence table?
- Does it have a `pending_review` workflow? This must be a real pending_review workflow, not
  only an ad hoc note field.
- Can it store `source_url`?
- Can it store a structured citation object?
- Can it store `source_snapshot_hash`, `content_sha256`, `hashes_match`, and integrity warnings?
- Can it distinguish evidence from decisions?
- Can it block automatic approval/publication when integrity warnings exist?
- Does it already have a review/admin UI, or only a database state?

## Integration Shape

If candidates, evidence, citation storage, integrity fields, and `pending_review` already exist,
TASK-004B can be a direct read-only integration pilot.

If any of those primitives are missing, TASK-004B must start by adding the downstream candidate
and evidence model. In that case, `official-sources` should remain unchanged and continue to act
only as read-only official evidence infrastructure.

## Required Boundary

`official-sources` must not approve, publish, rank, classify legal meaning, decide eligibility,
or write into the downstream project. The downstream project owns review, decisions, publication,
and user-facing workflow.

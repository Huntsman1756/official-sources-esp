# Downstream Import Checklist

Use this checklist before any downstream project imports `official-sources` evidence.

This checklist applies to EduAyudas, `la-ayuda`, and future downstream projects. It is deliberately
conservative: importing official evidence must not publish, approve, or create public records by
itself.

## 1. Preview First

- Validate the evidence contract in preview mode before writing anything.
- Confirm there are no local paths, secrets, VPS details, or raw legal-text dumps in the payload.
- Confirm `source_code`, `official_identifier`, `official_url`, citation, and integrity fields are present.
- Treat preview failures as blockers.

## 2. Write Evidence Only

- First write only to downstream evidence staging.
- Do not create downstream source candidates in the same step unless the task explicitly says so.
- Evidence staging must preserve:
  - `official_identifier`;
  - `official_url`;
  - `citation_json`;
  - `source_snapshot_hash`;
  - `content_sha256`;
  - `hashes_match`;
  - `has_integrity_warning`;
  - `integrity_warning_reason`;
  - artifact availability.

## 3. Block Integrity Warnings

- `hashes_match=false` must block automatic downstream use.
- `has_integrity_warning=true` must block automatic downstream use.
- Integrity warnings require human review and should remain visible in downstream staging.
- Do not silently drop or rewrite integrity fields.

## 4. Create Source Candidates After Evidence Staging

- Create downstream source candidates only after evidence staging exists.
- Candidate status must default to `pending_review` or the downstream equivalent.
- `accept_for_downstream_pilot` and `likely_relevant` are not approvals.
- Candidate creation must not create public pages or active records.

## 5. Create Drafts Only After Review

- Draft creation must be a separate step after evidence/candidate review.
- Draft records must be non-public by default.
- Drafts must keep citation and integrity links back to evidence staging.
- Missing fields must remain marked as pending review instead of being invented.

## 6. Never Publish On Import

- Import must never set public, active, approved, reviewed, or published status.
- Publication must remain downstream-owned and outside `official-sources`.
- Downstream-specific publication rules must be explicit, tested, and separate from import logic.
- A successful import means evidence is staged, not that the downstream record is valid for users.

## 7. Keep Publication Rules Downstream-Specific

- `official-sources` provides provenance, citation, integrity, artifacts, and candidate review metadata.
- Downstream projects decide product fit, editorial readiness, approval, and publication.
- Do not use a generic `acceptCandidate` path that bypasses official-source review.
- Do not route raw legal text to public pages by default.

## 8. Final Pre-Commit Check

Before committing an import task, verify:

- no public records were created unless explicitly requested in a later publication task;
- no raw artifacts, local temp files, `.env`, databases, or caches are staged;
- no downstream status was promoted beyond review-safe values;
- validation commands actually ran and their results are documented;
- the report states whether publication remains blocked.

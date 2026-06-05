# EduAyudas Real Evidence Package Readiness

Date: 2026-06-04

Task: `TASK-EDUAYUDAS-OFFICIAL-SOURCES-REAL-PACKAGE-001`

Scope: documentation-only readiness audit from `official-sources` for the first real EduAyudas
evidence package.

No downstream repository was modified. No imports, database writes, live source fetches, monitor
previews, candidate creation, evidence-grade promotion, aid draft creation, publication, VPS,
Hermes, or systemd operations were performed.

## Verdict

GO for a narrow BOE-only evidence package readiness path.

NO-GO for a broad BDNS/BOE/autonomous package in the next implementation step.

Reason: `official-sources` already has a review-only EduAyudas evidence-packet profile covering
`BDNS`, `BOE`, `BOJA`, `BOCYL`, `BOCM`, and `DOGV`, but the current EduAyudas downstream evidence
schema and database migration only accept `BOE` as `source_code`. BDNS and autonomous bulletin
items must stay as future source requirements until EduAyudas extends its evidence schema and import
contract.

## Current Upstream Profile

Implemented MCP entrypoint:

```text
build_evidence_packet
```

Current output is a planning/profile response, not a generated evidence file:

```text
status=ok
resource_type=evidence_packet_profile
consumer=eduayudas
profile=education_aid
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
staging_only=true
packet_status=profile_only
```

With an `official_identifier`, the tool returns a review target only:

```text
evidence_status=not_evidence
candidate_status=not_candidate
review_status=manual_review_required
stored_metadata_status=not_loaded_by_this_planning_tool
```

It does not fetch the source, load stored metadata, download artifacts, write JSONL, create
evidence-grade records, create candidates, or import into EduAyudas.

## Source Scope

Current upstream source status for the EduAyudas profile:

| Source | Operational status | Monitor support | MCP support | Candidate allowed | Evidence-grade allowed | Role |
| --- | --- | --- | --- | --- | --- | --- |
| `BDNS` | `metadata_adapter_validated` | available | false | false | false | Primary grants registry family, but not downstream-importable yet. |
| `BOE` | `metadata_adapter_validated` | available | true | false | false | Only current realistic first evidence package source. |
| `BOJA` | `metadata_adapter_validated` | available | false | false | false | Future autonomous evidence source after downstream schema review. |
| `BOCYL` | `metadata_adapter_validated` | available | false | false | false | Future autonomous evidence source after downstream schema review. |
| `BOCM` | `monitor_validated` | available | false | false | false | Future autonomous evidence source; monitor metadata is not evidence. |
| `DOGV` | `metadata_adapter_validated` | available | false | false | false | Future autonomous evidence source after downstream schema review. |

## Downstream Contract Found

EduAyudas currently exposes these scripts:

```text
npm run official-sources:preview -- --file path/to/evidence.json
npm run official-sources:preview -- --file path/to/evidence.json --write-evidence
npm run official-sources:create-candidates -- --evidence-ids ID1,ID2
npm run official-sources:create-candidates -- --evidence-ids ID1,ID2 --write-candidates
npm run official-sources:create-aid-draft -- --candidate-id 11
npm run official-sources:create-aid-draft -- --candidate-id 11 --write-draft
```

Safe interpretation:

- preview mode validates evidence JSON and performs no writes;
- `--write-evidence` writes only to `official_source_evidence`, local/dev guarded;
- `--write-candidates` converts explicit evidence IDs only into `source_candidates`;
- `create-aid-draft` is a later dry-run-first pilot path, explicitly scoped to selected candidates;
- none of these commands publishes an aid or approves eligibility.

## Downstream Format Constraint

The EduAyudas Zod schema currently uses:

```text
officialSourcesSourceCodeSchema = BOE only
```

Migration `016_official_source_evidence` also constrains:

```text
source_code IN ('BOE')
```

Therefore the first real package should be BOE-only unless a separate EduAyudas task expands:

- `officialSourcesSourceCodeSchema`;
- `official_source_evidence.source_code`;
- mapping from upstream source families to downstream evidence rows;
- preview/write tests for each new source family;
- migration/state confirmation for staging before any write mode.

## Required Evidence JSON Shape

Current EduAyudas evidence files require the downstream schema shape:

```text
source_code
resource_type
official_identifier
title
publication_date
version_date
official_url
citation
integrity
artifacts
official_sources_candidate
```

Nested requirements include:

```text
citation.source_code
citation.resource_type
citation.official_identifier
citation.title
citation.official_url
citation.publication_date
citation.version_date
integrity.source_snapshot_hash
integrity.content_sha256
integrity.hashes_match
integrity.last_integrity_check_at
integrity.content_changed_at
integrity.has_integrity_warning
integrity.integrity_warning_reason
artifacts.xml_available
artifacts.html_available
artifacts.pdf_available
official_sources_candidate.candidate_id
official_sources_candidate.manual_decision
official_sources_candidate.evidence_label
official_sources_candidate.evidence_review_status
official_sources_candidate.downstream_project_fit
```

Current accepted values imply a reviewed upstream evidence candidate, not an automatic product
record.

## First Package Recommendation

The next implementation should build one fixture-grade BOE evidence JSON package from already
stored/reviewed `official-sources` evidence, then run only the EduAyudas preview command.

Minimum acceptable package:

```text
source_code=BOE
resource_type=official_document
official_identifier=BOE-A-YYYY-NNNNN
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
downstream_project_fit=EduAyudas
integrity.hashes_match=true
integrity.has_integrity_warning=false
```

Allowed first validation:

```text
npm run official-sources:preview -- --file path/to/evidence.json
```

Blocked in the first validation PR:

- `--write-evidence`;
- `--write-candidates`;
- `--write-draft`;
- production or staging writes;
- BDNS package rows;
- BOJA/BOCYL/BOCM/DOGV package rows;
- new EduAyudas migrations;
- publication, eligibility, amount, deadline, or application-channel claims.

## Required Follow-Ups

1. `TASK-EDUAYUDAS-OFFICIAL-SOURCES-BOE-PACKAGE-PREVIEW-001`
   Build a BOE-only evidence JSON file and run EduAyudas preview mode only.

2. `TASK-EDUAYUDAS-OFFICIAL-SOURCES-EVIDENCE-SCHEMA-EXPANSION-001`
   Only after BOE preview is stable, decide whether to extend EduAyudas schema beyond `BOE`.

3. `TASK-EDUAYUDAS-OFFICIAL-SOURCES-BDNS-AUTONOMIC-PACKAGE-001`
   Only after schema expansion, add BDNS/autonomous evidence package rows with product-side tests.

## Final Boundary

`official-sources` is ready to guide the first EduAyudas real package. It is not yet ready to
generate that package from `build_evidence_packet` alone, and EduAyudas is not yet ready to consume
the full upstream source family matrix.

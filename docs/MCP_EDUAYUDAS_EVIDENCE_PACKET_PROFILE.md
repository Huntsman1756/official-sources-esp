# MCP Eduayudas Evidence Packet Profile

Date: 2026-05-31

Task: `TASK-MCP-EVIDENCE-PACKETS-EDUAYUDAS-001`

This contract defines the first review-only education-aid evidence packet profile for `eduayudas`.

It is a planning profile. It does not generate product aids, publish content, create candidates,
promote records to evidence-grade, download artifacts, fetch live sources, write JSONL, or write to
`G:\_Proyectos\eduayudas\`.

## Source Priority

| Source | Source family | Role |
| --- | --- | --- |
| `BDNS` | grants registry | Primary official convocatoria registry for education-aid discovery. |
| `BOE` | state bulletin | State official bulletin and citation source. |
| `BOJA` | autonomous bulletin | Andalusia education-aid evidence source. |
| `BOCYL` | autonomous bulletin | Castilla y Leon education-aid evidence source. |
| `BOCM` | autonomous bulletin | Madrid education-aid evidence source. |
| `DOGV` | autonomous bulletin | Valencian education-aid evidence source. |

Education portals and sedes remain missing source families until mapped through explicit
source-specific work. BDNS concessions/awards are not global evidence inputs: they may be previewed
or ingested only for one `--num-conv` at a time, with beneficiary fields redacted by default unless
an explicit privacy-reviewed operation approves including them.

## Required Packet Fields

```text
consumer
profile
source_code
source_family
official_identifier
official_url
title
publication_date
issuing_body
jurisdiction
retrieved_at
reviewed_at
evidence_status
candidate_status
review_status
```

## Safety

Every `build_evidence_packet` response must preserve:

```text
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
```

Consumers must not infer:

- aid created;
- aid published;
- eligibility decided;
- evidence-grade record;
- product acceptance.

Evidence packet planning is not evidence generation. Product-side review remains mandatory.

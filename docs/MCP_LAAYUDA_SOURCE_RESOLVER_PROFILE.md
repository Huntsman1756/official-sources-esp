# MCP La-Ayuda Source Resolver Profile

Date: 2026-05-31

Task: `TASK-MCP-BENEFIT-SOURCE-RESOLVER-LAAYUDA-001`

This contract defines the first read-only source-lead resolver profile for `la-ayuda`.

It returns official source leads and missing source families for manual review. It does not resolve
legal meaning, decide eligibility, verify amounts or deadlines, create Markdown, publish benefit
pages, fetch arbitrary URLs, or write to `G:\_Proyectos\la-ayuda\`.

## Supported Topics

```text
benefits
housing
family
dependency
disability
social_services
```

## Registered Source Leads

The initial resolver profile uses registered official source families already present in
`official-sources`:

```text
BOE
BDNS
BOCM
BOJA
DOGV
BOCYL
```

Depending on topic, BDNS may be omitted where grants/subsidies are not the primary source family.

## Missing Source Families

The resolver may return missing source-family entries such as:

```text
official_portals
sede_electronica
housing_portals
social_services_portals
dependency_portals
disability_portals
```

These entries are planning gaps. They are not verified official URLs.

## Safety

Every `resolve_normative_reference` response must preserve:

```text
status=manual_review_required
mode=read_only
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
exact_reference_resolved=false
```

Consumers must not infer:

- benefit page approved;
- eligibility decided;
- amount or deadline verified;
- publication-ready status;
- legal meaning decided.

Manual review is required before any downstream citation, Markdown update, or public product use.

# Autonomous and Provincial Source Audit Synthesis - 2026-05-21

## Scope

This synthesis integrates four audit-only branches:

- `agent/audit-north`
- `agent/audit-west`
- `agent/audit-islands`
- `agent/audit-provincial`

No adapters were implemented. No VPS was touched. No database was touched. No
candidates were created. No backfills were run. No downstream projects were
touched. The merged work is documentation only.

## Source Reports

- `docs/reports/AUTONOMOUS_NORTH_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/AUTONOMOUS_WEST_CENTRAL_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/AUTONOMOUS_ISLANDS_MEDITERRANEAN_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/PROVINCIAL_BULLETIN_STRATEGY_AUDIT_2026-05-21.md`

## Sources Audited

New autonomous/statutory territory sources audited in this batch: 16.

| Batch | Sources |
| --- | --- |
| North / northeast | DOGC, BOA, BON, BOPV/EHAA, BOR |
| West / central | BOPA, DOG, DOE, BOCYL, DOCM |
| Islands / Mediterranean / statutory cities | BOIB, BOC Canarias, BOC Cantabria, BORM, BOCCE, BOME |

Together with prior BOJA, BOCM, and DOGV work, the project now has at least an
audit or implementation path for the 19 autonomous/statutory territory sources
tracked in `docs/OFFICIAL_BULLETIN_REGISTRY.md`.

## Cross-Source Ranking

Top new autonomous/statutory P1 candidates:

| Rank | Source | Why |
| --- | --- | --- |
| 1 | BOCYL Castilla y Leon | Official JCyL open-data API returns structured records with issue metadata and PDF/XML/HTML links. Low to medium expected complexity. |
| 2 | BOPV/EHAA Pais Vasco | Official REST/OpenAPI surface with stable administrative-act IDs and direct artifact links. Low to medium expected complexity. |
| 3 | BOIB Illes Balears | Official issue pages expose document PDF, HTML, and XML alternate versions with ELI-style URLs. Low expected complexity. |
| 4 | BOR La Rioja | Official XML API and explicit no-publication behavior. Low expected complexity once endpoint examples are pinned from the API document. |
| 5 | BOC Canarias | Stable issue/document identifiers, clean issue HTML, PDFs, and RSS. Low to medium expected complexity, but XML was not confirmed. |
| 6 | DOE Extremadura | Strong metadata and official XML/PDF availability, but exact XML link extraction and issue suffix normalization need fixtures. |

Best next new autonomous MVP candidate:

```text
BOCYL metadata-only MVP
```

Reason: it has the cleanest combination of official structured JSON discovery,
stable document IDs, and official PDF/XML/HTML artifact URLs. This should still
be source-indexing only: one date/issue, raw JSON/XML hashing, no candidates, no
bulk PDFs, and no backfill.

Strong alternate if BOCYL is deferred:

```text
BOPV/EHAA metadata-only MVP
```

Reason: the official OpenAPI surface is strong, and BOPV/EHAA is a good
API-led complement to the existing BOJA/DOGV/BOCM work.

## Defer / High-Risk Sources

Best deferred source:

```text
BOCCE Ceuta
```

Reason: it is valid and official, but the observed surface is mostly
Joomla/JDownloads listings and issue PDFs. Per-document HTML/XML/API structure
was not confirmed, so a document-level adapter would likely become PDF
segmentation work too early.

Other high-risk or lower-priority sources:

| Source | Risk |
| --- | --- |
| DOCM Castilla-La Mancha | NID is strong, but discovery/detail behavior appears brittle and PDF-first. |
| Alicante BOP | Stable document IDs and static result links were not confirmed in the sample. |
| BOA Aragon | Legacy CGI is usable, but document ID normalization needs a focused fixture pass. |
| BON Navarra | HTML routes and announcement codes are usable, but no public XML/API/RSS was confirmed. |
| BOME Melilla | Good CVE-like IDs and HTML/PDF, but no public XML/API/RSS and pre-2018 archive split. |
| Sevilla BOP | Issue/CVE monitoring is realistic, but document extraction was not confirmed from static fetch. |

## Provincial Bulletin Strategy

Do not build one generic BOP adapter first.

The BOE "Otros diarios oficiales" page is the authoritative inventory seed, but
the provincial bulletin landscape is technically heterogeneous. The right shape
is:

1. Maintain a BOE-seeded inventory with verification date, observed formats, and
   technical family.
2. Build metadata-only monitoring for a small sample with stable IDs and
   readable indexes.
3. Add platform-specific adapters only after metadata monitoring proves stable.
4. Add oposiciones-only filtering after metadata quality is validated.
5. Defer PDF-first, browser-friction, and unknown/manual portals.

Best first BOP metadata-monitor pilots:

| Priority | Province | Rationale |
| --- | --- | --- |
| 1 | Barcelona | HTML index, stable register IDs, and official RSS/open-data surface. |
| 2 | A Coruna | Latest issue and previous bulletin pages expose document IDs, PDF, and HTML. |
| 3 | Malaga | Calendar/index with visible edict IDs and document PDF links. |
| 4 | Bizkaia | RSS/search/CVE looks promising, but dynamic filters need focused verification. |
| 5 | Valencia | Stable register numbers and download links; portal-specific implementation needed. |

Madrid and Murcia should stay out of the provincial adapter scope because the BOE
provincial list does not classify them as BOPs; they are covered by BOCM and
BORM respectively in autonomous-source work.

## Recommended Next 3 Tasks

1. `TASK-AUTO-BOCYL-001 - BOCYL endpoint fixture discovery`
   - Verify one date, one no-publication date, JSON API filtering, and the
     official PDF/XML/HTML artifact links for a small set of records.
   - Output: docs-only fixture report and MVP adapter plan.

2. `TASK-AUTO-BOPV-001 - BOPV/EHAA API fixture discovery`
   - Verify API pagination/filter semantics, language suffixes, issue-summary
     reconciliation, and raw JSON hash strategy.
   - Output: docs-only fixture report and MVP adapter plan.

3. `TASK-BOP-MONITOR-001 - Provincial metadata monitor design`
   - Design a metadata-only monitor for Barcelona, A Coruna, and Malaga.
   - Output: internal spec only; no adapters, no database writes, no candidates.

## Implementation Guardrails

Any next adapter MVP should remain metadata/index-only until separately approved:

- fetch one explicit date or issue;
- parse official metadata and official artifact URLs;
- compute SHA-256 over raw official payloads;
- store no candidates;
- download no PDFs by default;
- run no backfills;
- touch no VPS unless a later deployment task explicitly requires it.

## Integration Result

The four audit branches were reviewed as docs-only branches and merged without
conflicts. The integrated report set gives enough evidence to choose the next
autonomous MVP candidate and to avoid prematurely generalizing provincial BOPs.

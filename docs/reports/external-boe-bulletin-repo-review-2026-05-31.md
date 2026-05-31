# External BOE and bulletin repository review - 2026-05-31

Scope: review open GitHub repositories that can improve BOE, autonomous bulletin, or provincial
bulletin coverage without importing unrelated product/downstream behavior.

Reviewed repositories:

- `ComputingVictor/MCP-BOE` (`MIT`): useful MCP surface map for BOE consolidated legislation
  search, daily summaries, BORME summaries, and BOE auxiliary tables.
- `AnCode666/boe-mcp` (`MIT`): confirms the BOE consolidated search endpoint,
  `/datosabiertos/api/legislacion-consolidada`, and auxiliary table endpoint family,
  `/datosabiertos/api/datos-auxiliares/{table}`.
- `rOpenSpain/BOE` (`MIT`): useful for BOE/BORME identifier and URL conventions, especially
  `BOE-S`, `BOE-A`, `BOE-B`, and `BORME-S` shapes.
- `AxierSangroniz/bop-valladolid-pipeline` (no license detected): useful only as endpoint and
  selector prior art for the Valladolid provincial bulletin.

Decision:

- BOE: no direct code import. The local BOE adapter is stricter on no-publication handling,
  retry/backoff, artifact scoping, and cache boundaries. The most useful follow-up is a local
  review-only BOE auxiliary/consolidated-search feature, not replacement of the existing adapter.
- BORME: keep deferred. The external code proves demand and URL shapes, but production evidence
  should be built separately because BORME is not yet part of the local evidence-grade source set.
- BOP Valladolid: promoted from inventory-only to a metadata-only HTML monitor using the official
  date-scoped Liferay URL pattern observed in the external pipeline. PDF links remain official URLs
  only; no PDFs are downloaded and no candidate/evidence records are created.

Implemented from this review:

- Added `BOP_VALLADOLID` HTML monitor support.
- Updated `config/sources.yaml` to `monitor_validated` / `monitor_support=available`.
- Added parser and fixture coverage for Valladolid current-bulletin announcements.

Boundaries preserved:

- No PDF/artifact downloads.
- No LLM classification.
- No downstream writes.
- No candidate or evidence-grade promotion.

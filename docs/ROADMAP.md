# Roadmap

## Implemented / Current

Status: Completed for initial local infrastructure.

Scope:

- Tier 1: BOE daily publications.
- Tier 1: BOE controlled XML/HTML/PDF artifacts.
- Tier 1: BOE consolidated legislation.
- Tier 1: BOE consolidated index/block retrieval.
- Operational: CLI, systemd templates, migrations, backup/restore guide.
- BOE summary ingestion.
- Normalized storage.
- Ingestion audit.
- Citation layer.
- Integrity layer.
- Read-only MCP.
- Controlled artifact download.
- Operational CLI.
- Download audit.
- Read-only consolidated legislation retrieval by identifier.
- Official consolidated legislation text index retrieval.
- Official consolidated legislation text block retrieval.
- Block-level official citation support.
- SQLite schema migrations and persistent database validation.
- SQLite backup command and manual restore guide.
- Verified SQLite backup with default `quick_check`, optional `--full-check`, row-count comparison, and minimum size checks.
- Conservative BOE HTTP retry/backoff policy with request audit fields.
- MCP no-auth/private-only warning and tool output trust model.
- Downstream consumption contract.
- Controlled BOE summary range ingestion.
- Metadata-only keyword candidate prefiltering with safe dry-run mode, deterministic scoring,
  section/department filters, and a refined `la-ayuda` / `EduAyudas` profile.
- Structured cache-miss responses for read-only consumers.
- Status output split between summary HTTP status and artifact HTTP status.
- Pre-deploy VPS checklist.
- ADR-001 official publication hierarchy.
- Downstream onboarding kit for reusable project integrations.
- BOCM metadata-only adapter MVP.
- DOGV metadata-only adapter MVP and controlled 30-day metadata backfill.
- BDNS metadata-only adapter MVP for public grant calls (`convocatorias`).

## Not Implemented

- Tier 2: autonomous/statutory territory bulletins beyond BOJA and BOCM metadata pilots.
- Tier 3: provincial/local bulletins.
- Tier 4: EUR-Lex/DOUE.
- TED/OJ S procurement adapter.
- RAG/vector search.
- Full BOE historical backfill automation.
- Downstream integrations.
- Automatic candidate creation from prefilter dry-runs without explicit operator approval.
- Authentication for MCP or a public API.
- Legal interpretation.
- Automatic approval.
- Automatic publication.

## Follow-up - Persistent database operations

Status: Completed for lightweight SQLite operations by TASK-003D.

Completed:

- Ordered schema migrations.
- Migration checksum tracking.
- `db status`, `db migrate`, and `db validate` CLI commands.
- Upgrade tests from older SQLite schema states.
- `db backup` command.
- Manual backup and restore guide.
- Realistic restore, migrate, validate, and read-query smoke test.

Potential future scope:

- More detailed schema diagnostics.
- Optional backup timer templates.

## Follow-up - BOE consolidated legislation expansion

Status: Partially completed by TASK-003B.

Completed:

- Official text index retrieval by identifier.
- Official text block retrieval by identifier and official block ID.
- Block-level citation metadata.

Potential future scope:

- Official consolidated-law search if safely constrained and separately approved.
- Additional official metadata subroutes.
- ELI lookup only if a future task requires it.

Excluded unless separately specified:

- Own legal version diffing.
- Legal interpretation.
- RAG.

## Future phase - Autonomous bulletins

Status: BOJA pilot closed through reviewed evidence decisions.

Coverage registry:

- `docs/OFFICIAL_BULLETIN_REGISTRY.md`
- `docs/reports/OFFICIAL_BULLETIN_REGISTRY_2026-05-21.md`

Latest audit:

- `docs/reports/AUTONOMOUS_BULLETIN_SOURCE_AUDIT_2026-05-20.md`
- `docs/reports/BOCM_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/BOCM_DATE_TO_ISSUE_DISCOVERY_2026-05-21.md`
- `docs/reports/DOGV_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/AUTONOMOUS_NORTH_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/AUTONOMOUS_WEST_CENTRAL_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/AUTONOMOUS_ISLANDS_MEDITERRANEAN_SOURCE_AUDIT_2026-05-21.md`
- `docs/reports/PROVINCIAL_BULLETIN_STRATEGY_AUDIT_2026-05-21.md`
- `docs/reports/AUTONOMOUS_AND_PROVINCIAL_SOURCE_AUDIT_SYNTHESIS_2026-05-21.md`

Recommended first implementation:

- `TASK-AUTO-002 - BOJA adapter MVP` - implemented.

Future autonomous/statutory territory adapter MVPs must start metadata/index-only until separately approved. Do not create candidates, download large PDFs, write downstream evidence, or implement publication decisions in a first adapter MVP.

## Future phase - Grants registry sources

Status: BDNS source audit completed and metadata-only adapter MVP implemented for convocatorias.

Latest audit:

- `docs/reports/BDNS_SOURCE_AUDIT_2026-05-21.md`

Completed:

- `TASK-BDNS-002 - BDNS metadata adapter MVP`

Recommendation:

- `TASK-BDNS-003 - Controlled BDNS latest calls ingestion`

BDNS should be treated as a primary grants/subsidies registry, not as another bulletin. Initial
implementation is metadata-only and focused on convocatorias, raw JSON hashing, official
identifiers, citation metadata, and strict pagination/date caps. Candidate extraction, concessions,
bulk historical backfills, and downstream exports require separate approval.

Latest BOJA pilot result:

- 30-day BOJA metadata window: `1500` documents.
- Limited BOJA candidates created: `25`, all `human_review_required`.
- Selected BOJA PDF evidence candidates: `10`.
- BOJA PDFs downloaded by explicit candidate IDs: `10`.
- Evidence decisions applied: `4` accepted for downstream pilot, `6` out of scope.
- Downstream writes, approvals, and publications: `0`.

Recommended next step:

- `TASK-PLATFORM-001 - Downstream onboarding kit for official-sources` - completed.

Do not import BOJA evidence into EduAyudas until the downstream onboarding contract and
environment-safe import path are documented.

Recommended next platform/downstream step:

- `TASK-LAAYUDA-FOUNDATION - add evidence/candidate staging model`.

Recommended next autonomous-source option:

- DOGV candidate dry-run. The DOGV metadata MVP and controlled 30-day metadata backfill are
  validated with no PDFs, candidates, or downstream writes. BOCM remains paused on the incomplete
  metadata-only backfill because `2026-05-06` still fails from the VPS.

Recommended next new autonomous-source MVP after current validated-source work:

- BOCYL metadata-only MVP. Endpoint fixture discovery is complete in
  `docs/reports/BOCYL_ENDPOINT_FIXTURE_DISCOVERY_2026-05-21.md`; BOCYL has an official JCyL
  open-data API with stable document identifiers and PDF/XML/HTML artifact links.
- BOPV/EHAA metadata-only MVP is the strongest alternate API-led candidate.
- Provincial BOP work should remain metadata-monitor design only until Barcelona, A Coruna, and
  Malaga prove stable as pilot sources.

## Future phase - EUR-Lex

Status: Not started.

## Future phase - RAG/search

Status: Not started.

## Future phase - Git/Markdown export

Status: Not started.

## Future phase - Downstream integrations

Status: Onboarding contract documented. EduAyudas has a validated local/dev path; no production
downstream rollout is implemented.

Current platform status as of 2026-05-21:

- BOE is validated as the mature Tier 1 source and has exported reviewed downstream evidence.
- BOJA is validated as the first autonomous metadata-first source through reviewed PDF evidence
  decisions, with no downstream import.
- EduAyudas integration is validated as a downstream pattern, but current EduAyudas product QA is
  being repaired in that downstream repo by another agent.
- `la-ayuda` has validated evidence staging, candidate staging, non-public draft creation, and
  internal review without generating a public route.
- `docs/reports/OFFICIAL_SOURCES_PLATFORM_STATUS_2026-05-21.md` records the current strategic
  state and next options.

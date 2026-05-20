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

## Not Implemented

- Tier 2: autonomous/statutory territory bulletins.
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

Latest audit:

- `docs/reports/AUTONOMOUS_BULLETIN_SOURCE_AUDIT_2026-05-20.md`

Recommended first implementation:

- `TASK-AUTO-002 - BOJA adapter MVP` - implemented.

Future autonomous/statutory territory adapter MVPs must start metadata/index-only until separately approved. Do not create candidates, download large PDFs, write downstream evidence, or implement publication decisions in a first adapter MVP.

Latest BOJA pilot result:

- 30-day BOJA metadata window: `1500` documents.
- Limited BOJA candidates created: `25`, all `human_review_required`.
- Selected BOJA PDF evidence candidates: `10`.
- BOJA PDFs downloaded by explicit candidate IDs: `10`.
- Evidence decisions applied: `4` accepted for downstream pilot, `6` out of scope.
- Downstream writes, approvals, and publications: `0`.

Recommended next step:

- `TASK-PLATFORM-001 - Downstream onboarding kit for official-sources`.

Do not import BOJA evidence into EduAyudas until the downstream onboarding contract and
environment-safe import path are documented.

## Future phase - EUR-Lex

Status: Not started.

## Future phase - RAG/search

Status: Not started.

## Future phase - Git/Markdown export

Status: Not started.

## Future phase - Downstream integrations

Status: Not started.

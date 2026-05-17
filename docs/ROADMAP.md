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
- Metadata-only keyword candidate prefiltering.
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

Status: Not started.

## Future phase - EUR-Lex

Status: Not started.

## Future phase - RAG/search

Status: Not started.

## Future phase - Git/Markdown export

Status: Not started.

## Future phase - Downstream integrations

Status: Not started.

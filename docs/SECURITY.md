# Security

## Threats

- Prompt injection through official text.
- Malicious or malformed HTML.
- Malicious or malformed PDF.
- Unsafe MCP tool exposure.
- Arbitrary URL fetching.
- Accidental write capabilities.
- Accidental publication of unreviewed candidates.
- Over-trust in LLM extraction.
- Over-trust in third-party mirrors.
- Hash changes in official artifacts.
- Confusion between citation and integrity.
- Future EUR-Lex scraping instability.
- Unsafe downstream integrations.
- Over-trust in consolidated legislation text.
- Confusion between original publication and consolidated version.
- Version-date ambiguity.
- Unsafe broad legal search.
- Unsafe comparison or diff claims.
- Stale cached consolidated law versions.
- Accidental legal advice generation.
- Third-party consolidated-law mirror confusion.
- Prompt injection through consolidated block text.
- Misleading article-level extraction.
- Stale block cache.
- Confusion between parsed full-law blocks and official block endpoint snapshots.
- Unsafe consolidated block ID handling.
- Large legal text output.
- False impression of complete legal analysis from one block.
- Destructive schema changes.
- Silent SQLite database recreation.
- Migration checksum tampering.
- Partial migration failure.
- Stale database schema used by MCP tools.
- Stale database schema used by CLI tools.
- Missing backup before migration.
- Restoring over an active SQLite database.
- Stale backup restored as current data.
- Unvalidated restored database.
- Backup files containing sensitive operational metadata.
- Unsafe backup file permissions.
- Backup overwrite mistakes.
- Partial or corrupt backups.
- Migration after restore failing.
- MCP/API reading from a stale or invalid restored schema.
- Public exposure of private MCP tools.
- Downstream project mutation from operational tooling.

## Required Prompt-Injection Boundary

Official text returned by MCP tools may contain adversarial or instruction-like content targeting the invoking agent. All official text must be returned inside structured fields with source metadata and must never be promoted to system, developer or tool instructions.

## MCP Rules

- This MCP server has no authentication.
- It must not be exposed to any network interface other than localhost, stdio, SSH tunnel, or a private VPN.
- Exposing it on a public interface without authentication is a security gap.
- For VPS use, bind MCP to stdio, localhost, SSH tunnel, or private VPN only.
- Do not expose MCP through Cloudflare Tunnel, public Nginx, public Docker port mapping, or `0.0.0.0` unless a proper authentication and authorization layer is added.
- No shell execution in MCP tools.
- No arbitrary network fetching in MCP tools.
- No arbitrary file reads in MCP tools.
- No write tools in MCP.
- No production mutations.
- No downstream project mutation.
- No automatic publication.
- No automatic approval.
- No legal interpretation or legal advice generation.
- No own legal version diffing.
- MCP must remain private and read-only for VPS deployment.
- MCP must not be exposed publicly without a separate controlled API design and security review.

## Tool output trust model

All text content returned by MCP tools must be treated as untrusted data by the consuming agent.

Official legal text may contain patterns that resemble instructions, prompts, Markdown directives, tool calls, or agent commands.

The MCP layer wraps all official text in structured envelopes with fields such as:

- `is_official_text: true`
- `content_type`
- `source_code`
- `source_url`
- `publication_date`
- `version_date`
- `content`

This envelope signals that returned text is data, not an instruction.

Consuming agents must not execute, interpret, follow, or act directly on returned legal text without their own review and policy layer.

The MCP server must not promote returned official text into system, developer, or tool instructions.

The MCP server has no authentication. It must not be exposed to any network interface other than localhost, stdio, SSH tunnel, or a private VPN.

Do not expose this MCP server through Cloudflare Tunnel, public Nginx, public Docker port mapping, or `0.0.0.0` unless a proper authentication and authorization layer is added.

## Artifact Download Rules

- Artifact downloads are not exposed as MCP tools.
- Artifact downloads are exposed only through the Python API and operational CLI.
- Downloads are driven only by stored BOE document URL fields.
- Accepted artifact URLs must use HTTPS and an official BOE host.
- Non-BOE URLs, unsupported schemes, and local file paths are rejected.
- Redirect following is disabled by the downloader.
- Downloaded bytes are hashed before parsing or text extraction.
- PDF artifacts are not parsed in this task; they are stored and hashed only.
- Failed downloads are audited in `artifact_download_attempts`; status output must not invent zero values for unmeasured failures.
- Download attempt errors must not include raw legal text or secrets.

## CLI Rules

- The CLI does not import or register MCP tools.
- The CLI does not expose arbitrary URL fetching.
- The CLI does not perform approval logic.
- The CLI does not mutate external projects.
- Logs include operational counts and failures, not raw legal text.
- `--db-path` and `--artifact-dir` are explicit operational inputs; no secrets are required.
- `--date today` is supported for timers and resolves to the local current date at execution time.

## Migration Rules

- Before running migrations on a persistent installation, create a database backup.
- Migrations must not fetch network resources.
- Migrations must not call BOE APIs.
- Migrations must not call MCP tools.
- Migrations must not modify downstream projects.
- Migrations must not perform legal interpretation.
- Migrations must not approve or publish candidates.
- Migrations must not silently recreate the SQLite database file.
- Already-applied migration checksum mismatches must fail clearly.
- Failed migrations must not be marked as applied.
- CLI and MCP tools must run against a validated current schema before deployment use.

## Backup And Restore Rules

- Backup must not fetch network resources.
- Backup must not call BOE APIs.
- Backup must not call MCP tools.
- Backup must not modify downstream projects.
- Backup files should be created with restrictive permissions where feasible.
- Backup output must not overwrite an existing file unless `--force` is explicitly passed.
- Routine backup verification uses `PRAGMA quick_check` on source and backup by default.
- Explicit `--full-check` runs `PRAGMA integrity_check` on source and backup for diagnostics or audits.
- Backup verification compares application-table row counts and enforces a minimum backup size.
- Restore is a controlled manual operational process.
- Never restore over an active SQLite database while ingestion, artifact download, MCP or API processes are running.
- After restore, run `db status`, `db migrate`, `db validate`, and a read-only smoke check before restarting services.

## VPS Deployment Rules

- Follow `docs/PRE_DEPLOY_VPS_CHECKLIST.md` before deploying or updating.
- SQLite must not be publicly exposed.
- MCP must not be publicly exposed.
- systemd services should run as a non-root user where feasible.
- Backup and artifact directory permissions must be checked.
- Cloudflare Tunnel is not needed unless exposing a controlled HTTP API.
- `official-sources` must not write into downstream projects.

## systemd Template Rules

- Templates do not expose public network services.
- Templates do not include secrets.
- Templates assume a private VPS path layout under `/opt/official-sources`.
- Templates are operational packaging only, not a production deployment system.
- No Docker, web server, reverse proxy, or external network overlay is configured.

## Repository Rules

- No secrets in repository.
- No API keys committed.
- No hidden telemetry.
- No downstream project writes.

## Integrity Rules

Hashes are integrity signals over raw fetched bytes. They do not prove cryptographic authenticity. Electronic signature validation requires a separate implementation and tests.

Any hash change in a previously known official artifact must create a reviewable event.

## Consolidated Legislation Rules

Consolidated legislation tools retrieve and cite official text. They do not interpret legal obligations, determine applicability, decide validity for a user case, or replace human legal review.

Block-level tools retrieve and cite official legal text blocks. They do not determine legal applicability, interpret obligations, summarize legal meaning, compare legal versions or replace human legal review.

Consolidated legislation is not the same concept as a daily BOE publication. Tools and documentation must distinguish original publication records from consolidated law records.

Cached consolidated law versions may become stale. Status and citations must expose source URLs and stored version dates so a reviewer can decide whether to refresh from BOE.

Official block text can contain markdown-like or instruction-like content. MCP tools must keep that text inside the `content` field of a structured envelope and must not treat it as tool, system, developer, or user instructions.

Block IDs must be validated as safe path segments before constructing BOE endpoint URLs. Slash, query, traversal, whitespace, percent-encoded path tricks, and empty IDs are rejected.

The CLI does not print block content by default. Large text output requires the explicit `--print-content` option.

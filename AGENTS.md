## Local Helper Router Policy

Before asking the user or reasoning independently on eligible tasks, invoke `G:\_Proyectos\scripts\local-helper-router.ps1` as a first pass.

Eligible task types:
- `summary`
- `extraction`
- `smell_scan`
- `docstring`
- `changelog_draft`

Not eligible:
- `architecture`
- `security_review`
- `debugging`
- `cross_file_refactor`
- any task requiring cross-file reasoning
- any task requiring external knowledge
- any task requiring a decision from the user

Invocation conditions:
- single file or single diff as input
- input must fit the profile limits declared in `G:\_Proyectos\scripts\local-helper-config.json`
- `task_type` must exist in `allowed_task_types`

Consume the router output only if `safe_to_use_as_draft` is `true`.

If the router returns `safe_to_use_as_draft = false`, exits non-zero, or fails for any reason, continue without the helper result.

Never block or delay a task waiting on the helper. The helper is an optional cheap first pass, not a required dependency.

@C:\Users\rome_\.codex\RTK.md

## Project VPS

- Always use VPS `157.90.22.40` for this project.
- Connect as `root@157.90.22.40`.
- Preferred SSH alias: `mcpspain-official-sources-vps`.

## AI Delegation Workflow

Codex is the orchestrator and reviewer. OpenCode may be used only as an implementation worker through `tools/delegate-opencode.ps1`.

Default workflow for non-trivial implementation tasks:

1. Codex reads `AGENTS.md`, `PROJECT_STATE.md`, `TASK_QUEUE.md`, and relevant docs first.
2. Codex defines the task boundary and validation criteria.
3. Codex delegates implementation with:

   ```powershell
   pwsh ./tools/delegate-opencode.ps1 -Task "<precise bounded task>"
   ```

4. The wrapper uses an isolated git worktree by default and writes prompt, log, and patch artifacts under `.ai/`.
5. Codex reviews `git status`, `git diff`, the `.ai/logs/` output, and the `.ai/patches/` patch before accepting any work.
6. Codex may amend small issues directly after review.
7. Codex runs repo-appropriate validation before commit, deploy, or VPS work.

OpenCode restrictions:

- Do not commit.
- Do not push.
- Do not deploy.
- Do not run VPS or database operations.
- Do not edit secrets, `.env` files, credentials, tokens, or unrelated config.
- Do not bypass permission prompts with dangerous flags.
- Do not modify downstream product repos or add downstream product writes from `official-sources`.

VPS/deployment remains a separate Codex-reviewed step. Use `mcpspain-official-sources-vps` / `root@157.90.22.40` only after the diff has been reviewed, validation has run, and the task explicitly requires VPS work.

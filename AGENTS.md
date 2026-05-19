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

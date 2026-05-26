# Hermes local fleet for official-sources

This scaffold prepares a local read-only Hermes fleet for `official-sources`.

It is intentionally not a commit/deploy/VPS worker. Codex remains the orchestrator and reviewer.
Hermes produces reports only.

## Rate-limit budget

Provider budget supplied by the operator:

- chat/text: 100 requests per minute
- maximum concurrent chat calls: 5
- embeddings: 60 requests per minute, batch size 32

This repo should default to:

```text
official-sources MaxParallel=3
```

Reason: one concurrent slot is already expected to be used by the esdata Hermes run, and one slot
is reserved for manual/headroom. If the other project is stopped, `MaxParallel=4` is the hard local
ceiling for this scaffold.

Embeddings are not used in phase 1. TTS/STT are not used.

## Models

- `qwen3.6`: structure audit, policy review, QA, writer.
- `gemma4`: source registry audit and RSS monitor scout.
- `qwen3-embedding`: deferred until there is a real retrieval/indexing task.

## Bootstrap

Set one API key environment variable before bootstrapping:

```powershell
$env:HERMES_OFFICIAL_SOURCES_API_KEY = "<provider key>"
```

If you intentionally want a different environment variable, pass `-FallbackApiKeyEnv`.

Then run from the repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\hermes-official-sources\bootstrap-profile.ps1
```

The profile is created at:

```text
C:\Users\rome_\.hermes-official-sources-auditor
```

The repo is mounted into Docker as `/repo:ro`, so Hermes can inspect the project but cannot write to
the repository from inside the container.

## Run

Default parallel scout run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\hermes-official-sources\fleet\run-nightly.ps1
```

Conservative sequential run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\hermes-official-sources\fleet\run-nightly.ps1 -Sequential -MaxParallel 1
```

Reports are written under:

```text
C:\Users\rome_\.hermes-official-sources-auditor\reports
```

## Boundaries

Hermes may:

- inspect the repository;
- inspect official-source policy docs;
- produce reports;
- identify small tasks for Codex/OpenCode;
- mark blockers and UNKNOWN.

Hermes must not:

- commit, push, deploy, or run VPS operations;
- create candidates;
- create evidence-grade records;
- download PDFs;
- write downstream product repos;
- change secrets or `.env` files;
- bypass Codex review.

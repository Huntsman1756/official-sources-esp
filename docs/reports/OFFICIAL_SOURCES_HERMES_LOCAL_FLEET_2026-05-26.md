# Official-sources Hermes local fleet - 2026-05-26

## Diagnosis

`official-sources` is not blocked because it lacks implementation workers. It is blocked mainly by
scope control: source registry, monitor discovery, candidate creation, evidence-grade records,
PDF downloads, downstream exports, VPS/DB work, and product decisions must stay separate.

The repo already has a safe Codex -> OpenCode delegation wrapper. Hermes should therefore sit
before Codex as a read-only auditor and work preparer, not as an autonomous code writer.

## Recommended phase 1 fleet

Profiles:

- `structure-auditor`: maps repo structure, docs, tests, active queue, and allowed next work.
- `source-registry-auditor`: reviews `config/sources.yaml` against adapters, tests, and docs.
- `rss-monitor-scout`: prepares `TASK-SOURCE-RSS-MONITOR-001`, with BOCYL first and BOE as a
  positive control.
- `evidence-policy-reviewer`: blocks scope creep between monitor, candidates, evidence, PDFs,
  downstream, VPS, and DB.
- `qa-reviewer`: reviews generated reports for overclaiming and missing proof.
- `writer`: produces the final human/Codex summary.

## Rate-limit policy

Given the shared API key limits:

```text
chat/text requests: 100 rpm
maximum concurrent chat calls: 5
embedding requests: 60 rpm
```

The default local limit for this repo is:

```text
MaxParallel=3
DelaySeconds=12
```

Rationale:

- one concurrent slot is reserved for the already-running `esdata` Hermes process;
- one slot is reserved as headroom for manual or recovery work;
- three independent read-only scouts can run in parallel without exhausting the hard limit;
- QA and writer run after scouts complete.

If the other project is stopped, `MaxParallel=4` is acceptable. Do not use 5 unless this is the
only active workload on the key.

## Model assignment

- `qwen3.6`: structure, policy, QA, writer.
- `gemma4`: registry and RSS scout.
- `qwen3-embedding`: deferred; only useful after a deliberate repo-report retrieval task exists.
- `kokoro` and `whisper`: not useful for this repo phase.

## Hard boundaries

Hermes may observe, compare, summarize, flag blockers, and draft tasks.

Hermes must not:

- modify repo files;
- create source candidates;
- create evidence-grade records;
- download PDFs;
- write downstream product repos;
- run VPS, DB, deploy, commit, or push operations;
- invoke OpenCode directly.

Codex remains the orchestrator/reviewer. If Hermes finds a task worth implementing, Codex should
turn it into a bounded task and use `tools/delegate-opencode.ps1` only after reviewing the boundary.

## Scaffold

The local fleet scaffold lives in:

```text
tools/hermes-official-sources/
```

The generated local profile target is:

```text
C:\Users\rome_\.hermes-official-sources-auditor
```

The Docker runner mounts the repository as read-only at:

```text
/repo:ro
```

This keeps Hermes useful for autonomous review while preventing accidental repo writes from inside
the container.

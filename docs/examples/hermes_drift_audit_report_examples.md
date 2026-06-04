# Hermes Drift Audit Report Examples

## GO

```text
VERDICT: GO

Observed:
- expected_head_sha: 9c672b3ca34fa795ae7fee5206a4247180ed6adb
- expected_head_sha_source: /etc/official-sources/hermes-audit-contract.yaml
- actual_head_sha: 9c672b3ca34fa795ae7fee5206a4247180ed6adb

Failed gates:
- none

Warnings:
- none

Required human action:
- none
```

## WARNING

```text
VERDICT: WARNING

Observed:
- expected_head_sha: None
- expected_head_sha_source: None
- actual_head_sha: 9c672b3ca34fa795ae7fee5206a4247180ed6adb

Failed gates:
- none

Warnings:
- external release contract unavailable; HEAD gate not enforced
- journal evidence unavailable for official-sources-boe-daily.service: permission denied

Required human action:
- grant narrow journal read access or keep the explicit WARNING
```

## NO-GO

```text
VERDICT: NO-GO

Observed:
- expected_head_sha: 9df078b1ae599bdeca8c573bddbb53ea6c33a16a
- expected_head_sha_source: /etc/official-sources/hermes-audit-contract.yaml
- actual_head_sha: a5c050b588fce8277247e9bcde3c446d852e784a

Failed gates:
- observed checkout HEAD is a5c050b588fce8277247e9bcde3c446d852e784a, expected 9df078b1ae599bdeca8c573bddbb53ea6c33a16a
- git worktree is dirty
- PROJECT_STATE date is 2026-05-31, expected >= 2026-06-02
- source count is 66, expected 67

Warnings:
- git ls-remote observed remote head differs from expected release SHA: a5c050b588fce8277247e9bcde3c446d852e784a
- journal evidence unavailable for official-sources-integrity-check.service: permission denied

Required human action:
- inspect VPS checkout and decide whether to fast-forward checkout
- inspect dirty diff on VPS before any release claim
- refresh PROJECT_STATE.md or lower the expected date only with evidence
- compare config/sources.yaml against the declared source contract
- grant narrow journal read access or keep the explicit WARNING
```

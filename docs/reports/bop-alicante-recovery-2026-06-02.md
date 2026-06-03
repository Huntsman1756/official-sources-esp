# BOP Alicante DNS Recovery

Date: 2026-06-02

Task: `TASK-BOP-ALICANTE-RECOVERY-2026-06-02`

## Verdict

`BOP_ALICANTE` no longer reproduces the DNS failure that caused its
`degraded/manual-review` runtime-health overlay.

Current decision:

```text
BOP_ALICANTE registry status: monitor_validated
BOP_ALICANTE degraded: false
BOP_ALICANTE degraded_reason: null
BOP_ALICANTE recovery: DNS resolver-dependent failure resolved on 2026-06-02
candidate_creation_allowed: false
evidence_grade_allowed: false
```

This is a recovery record for runtime health. It is not a candidate-creation,
evidence-grade, PDF/artifact, downstream-write, or product-readiness promotion.

## Original Failure

The degraded state was introduced after the 2026-05-27 health regression:

```text
normal preview result: httpx.ConnectError: [Errno 11002] getaddrinfo failed
affected host: sede.diputacionalicante.es
classification: resolver-dependent DNS instability
```

The parser and official endpoint were not shown to be broken. The earlier diagnostic found that
Google DNS-over-HTTPS resolved `sede.diputacionalicante.es` to `195.53.69.137`, and forcing that
official hostname to that address returned parser-compatible JSON.

Historical evidence:

```text
docs/reports/provincial-monitors-health-001-2026-05-27.md
docs/reports/bop-alicante-health-regression-2026-05-27.md
docs/reports/bop-alicante-degraded-dns-2026-05-27.md
```

## Recovery Evidence

Local DNS now resolves the official host:

```powershell
Resolve-DnsName sede.diputacionalicante.es
```

Result:

```text
sede.diputacionalicante.es A 195.53.69.137
```

Local landing check:

```powershell
rtk curl.exe -I --max-time 15 https://sede.diputacionalicante.es/consultas-bop/
```

Result:

```text
HTTP/1.1 200 OK
```

Local monitor preview against the date that previously reproduced the failure:

```powershell
rtk python -m official_sources.cli html monitor --source BOP_ALICANTE --date 2026-05-27 --limit 1
```

Result:

```text
command_started=html monitor source_code=BOP_ALICANTE date=2026-05-27 mode=preview records=1 discovery_metadata_only=true
candidate_status=not_candidate
evidence_status=not_evidence
document_id=3893
```

VPS DNS and landing check through the project alias:

```bash
ssh mcpspain-official-sources-vps "getent hosts sede.diputacionalicante.es; curl -I --max-time 15 https://sede.diputacionalicante.es/consultas-bop/"
```

Result:

```text
195.53.69.137 sede.diputacionalicante.es
HTTP/1.1 200 OK
```

VPS monitor preview from the canonical checkout:

```bash
ssh mcpspain-official-sources-vps "cd /opt/official-sources/app && .venv/bin/python -m official_sources.cli html monitor --source BOP_ALICANTE --date 2026-05-27 --limit 1"
```

Result:

```text
command_started=html monitor source_code=BOP_ALICANTE date=2026-05-27 mode=preview records=1 discovery_metadata_only=true
candidate_status=not_candidate
evidence_status=not_evidence
document_id=3893
```

Current-date preview on 2026-06-02 returned `records=0` without DNS or HTTP failure. That is not
treated as a degraded signal because the previously failing date returned a valid metadata-only
record from both local and VPS paths.

## Residual Risk

The original failure was DNS resolver-dependent. If the resolver used by the local machine or the
project VPS again loses `sede.diputacionalicante.es`, `BOP_ALICANTE` may need to return to
`degraded/manual-review`.

This recovery does not authorize:

```text
custom DNS-over-HTTPS resolver behavior
hard-coded IP routing
PDF/artifact downloads
candidate creation
evidence-grade output
downstream writes
product automation
```

## Registry Update

`config/sources.yaml` now records the recovery as source-level descriptor metadata:

```yaml
degraded: false
degraded_reason: null
recovery_note: "DNS resolver-dependent failure; resolved 2026-06-02. Local and VPS preview confirmed records=1 for 2026-05-27."
```

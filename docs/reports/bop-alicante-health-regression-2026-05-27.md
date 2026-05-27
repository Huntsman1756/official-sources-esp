# BOP Alicante Health Regression Diagnostic

Date: 2026-05-27

Task: `TASK-BOP-ALICANTE-HEALTH-REGRESSION-001`

## Verdict

`BOP_ALICANTE` remains a live official endpoint, but it is not healthy under the normal local
resolver path used by the monitor.

Operational decision:

```text
combined provincial health: NO-GO
BOP_ALICANTE status in healthy set: degraded/manual-review
monitor code fix: NO-GO
Wave 003: blocked until Alicante is recovered or explicitly excluded from the healthy set
```

No registry status change was made in this diagnostic. The current `monitor_validated` registry
entry is historical validation; the current live health check remains degraded because normal
monitor execution still fails before any HTTP response is received.

## Scope

Read-only diagnostics only:

```text
no writes
no --write
no data/html_monitor
no candidates
no evidence-grade records
no PDF/artifact downloads
no downstream writes
no VPS, Hermes, systemd, BOE timer, or integrity timer changes
no headless browser
no bypass
```

## Current Registry Endpoint

```text
source_code: BOP_ALICANTE
landing: https://sede.diputacionalicante.es/consultas-bop/
endpoint: https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php
mode: metadata-only HTML discovery
candidate_creation_allowed: false
evidence_grade_allowed: false
```

## Reproduction

Command:

```powershell
rtk python -m official_sources.cli html monitor --source BOP_ALICANTE --date 2026-05-27 --limit 1
```

Result:

```text
httpx.ConnectError: [Errno 11002] getaddrinfo failed
```

The failure happens during DNS/connection setup in `fetch_html`, before the parser sees a response.

## DNS Evidence

Local resolver path:

```text
Resolve-DnsName sede.diputacionalicante.es
result: no answer / timeout

nslookup sede.diputacionalicante.es
result: timeout through local DNS server 192.168.1.44
```

Public resolver contrast:

```text
Cloudflare DNS-over-HTTPS:
  sede.diputacionalicante.es -> SERVFAIL
  comment: EDE(22): No Reachable Authority at delegation diputacionalicante.es

Google DNS-over-HTTPS:
  sede.diputacionalicante.es -> 195.53.69.137
```

This indicates resolver-dependent DNS instability for `diputacionalicante.es`, not a parser failure.

## Endpoint Evidence

Forcing the hostname to the Google-resolved address keeps the normal HTTPS hostname/SNI and returns
the official page:

```powershell
rtk curl.exe -I --max-time 15 --resolve sede.diputacionalicante.es:443:195.53.69.137 https://sede.diputacionalicante.es/consultas-bop/
```

Result:

```text
HTTP/1.1 200 OK
content-type: text/html; charset=UTF-8
```

The configured endpoint also returns JSON for the previously validated date when using the same
hostname/IP resolution:

```powershell
rtk curl.exe --max-time 15 --resolve sede.diputacionalicante.es:443:195.53.69.137 "https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php?nemo=BOP_CON&param=...&usuario=-"
```

Result:

```text
28017 bytes
{"boletin":{"boletin":[{"registro":[{"sumario":["N\u00ba 96 del 25-05-2026"],...
```

The endpoint is therefore still structurally compatible with the existing parser.

## Official Landing Cross-Check

The public sedelectronica landing is reachable and still links to the same BOP consultation host:

```text
https://diputacionalicante.sedelectronica.es/info.0
  -> https://sede.diputacionalicante.es/consultas-bop/
  -> https://sede.diputacionalicante.es/buscador-bop-antiguos/
  -> https://sede.diputacionalicante.es/insercion-de-anuncios-y-edictos-en-el-bop/
```

No stable replacement endpoint was found during this bounded diagnostic.

## Conclusion

Classification:

```text
primary: resolver-dependent DNS instability
not supported by evidence: endpoint obsolete
not supported by evidence: parser regression
not supported by evidence: monitor contract drift
```

No code fix is applied because the available workaround would require one of:

```text
hard-coded IP routing
custom DNS-over-HTTPS resolver behavior inside the monitor
alternate operational resolver policy
```

Those are operational network-policy decisions, not safe source-specific parser fixes.

## Next Action

Keep `BOP_ALICANTE` out of the combined healthy set until one of these is true:

```text
normal local DNS resolution recovers and live preview passes
an explicit resolver policy is approved for this project
BOP_ALICANTE is formally marked degraded/manual-review in the registry contract
```

Do not open Wave 003 while the combined health gate is still `NO-GO`, unless Alicante is explicitly
excluded from the healthy set by a separate scoped decision.

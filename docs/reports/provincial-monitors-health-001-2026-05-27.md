# Provincial Monitors Health 001

Date: 2026-05-27

Task: `TASK-PROVINCIAL-MONITORS-HEALTH-001`

## Decision

Combined provincial monitor health is `NO-GO` until `BOP_ALICANTE` endpoint/DNS is reviewed.

Seven monitored provincial sources returned one metadata-only preview record. `BOP_ALICANTE` failed
on two attempts with a DNS resolution error for the validated backing endpoint host.

## Scope

Checked sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_LUGO
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
```

Commands used preview mode only:

```text
rtk python -m official_sources.cli html monitor --source <SOURCE> --date 2026-05-27 --limit 1
rtk python -m official_sources.cli rss monitor --source BOP_LUGO --date 2026-05-27 --limit 1
```

No command used `--write`.

## Results

| Source | Monitor | Result | Records | Statuses | Notes |
| --- | --- | --- | ---: | --- | --- |
| `BOP_A_CORUNA` | HTML | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Current date preview returned document `2026/3370`. |
| `BOP_ALBACETE` | HTML | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Current date preview returned document `297619`; PDF endpoint recorded as metadata only. |
| `BOP_ALICANTE` | HTML | FAIL | 0 | n/a | Two attempts failed with `httpx.ConnectError: [Errno 11002] getaddrinfo failed`. |
| `BOP_LUGO` | RSS | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Current RSS preview returned `BOP DE 27/05/2026`; feed summary contains PDF links as metadata only. |
| `BOP_BARCELONA` | HTML | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Current page preview returned register `202610096574`. |
| `BOP_MALAGA` | HTML | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Current page preview returned edict `1725/2026`. |
| `BOP_BIZKAIA` | HTML | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Landing plus public detail preview returned document `I-612`; PDF endpoint recorded as metadata only. |
| `BOP_VALENCIA` | HTML | OK | 1 | `not_candidate`, `not_evidence`, `unclassified` | Current page preview returned register `2026/06245`; `official_url` is `null` by design for JS/AJAX PDF actions. |

## Failure Detail

`BOP_ALICANTE` validated endpoint currently configured in the registry:

```text
https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php
```

Both health attempts failed before HTTP response handling:

```text
httpx.ConnectError: [Errno 11002] getaddrinfo failed
```

This health check does not change `BOP_ALICANTE` registry status. A separate source-specific,
read-only endpoint health task should verify whether the official backing endpoint moved, is
temporarily unavailable, or requires a registry URL correction.

## Safety

No writes were performed:

```text
data/html_monitor: absent
data/rss_monitor: absent
```

No operational surfaces were touched:

```text
VPS checkout: unchanged
Hermes config: unchanged
systemd: unchanged
timers: unchanged
BOE timer: unchanged
integrity timer: unchanged
downstream repositories: unchanged
candidate creation: not used
evidence-grade records: not used
PDF/artifact downloads: not used
```

## Next

Do not start Wave 003 from this health result alone. First resolve or explicitly defer
`TASK-PROVINCIAL-BOP-ALICANTE-ENDPOINT-HEALTH-001`.

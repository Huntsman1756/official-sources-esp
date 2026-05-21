# BOCM httpx vs curl Search-Day Diagnosis

Date: 2026-05-21

## Summary

`TASK-AUTO-BOCM-003E` compared BOCM `search_day` behavior from the VPS for the blocking date:

```text
2026-05-06
```

The task did not resume the backfill, create candidates, download PDFs, or touch downstream
projects.

## VPS State

```text
commit=93a761c
DB validation=valid
```

The exact adapter-generated request is:

```text
method=GET
url=https://www.bocm.es/search-day-month?field_date%5Bdate%5D=06%2F05%2F2026
headers=Accept: text/html,application/xhtml+xml
timeout=connect 10s, read 90s, write 30s, pool 10s
follow_redirects=true
http2=false
trust_env=true
client_lifetime=fresh client per request
```

## curl Probes

An earlier immediate bounded `curl` probe after the previous task had returned:

```text
status=200
time=0.492620
size=24069
resolved_url=https://www.bocm.es/boletin/bocm-20260506-106
```

During this task, the same endpoint did not respond reliably from the VPS.

Bounded curl probe:

```text
status=000
total=30.001554
connect=0.000000
starttransfer=0.000000
remote_ip=none
http_version=0
size=0
result=connection timed out
```

Repeated bounded curl probes:

```text
probe 1: status=000 total=10.002566 size=0
probe 2: status=000 total=10.002988 size=0
probe 3: status=000 total=10.002877 size=0
```

DNS during the Python probe resolved:

```text
www.bocm.es -> 195.77.128.44
IPv6: none
IPv4: 195.77.128.44
```

## httpx Variants

All variants were run inside the project venv on the VPS, against the same exact URL.

Proxy environment:

```text
no proxy environment variables observed
```

| variant | result | elapsed | exception |
| --- | --- | ---: | --- |
| current_adapter_like | failed | 15.089s | ConnectTimeout: timed out |
| curl_like_headers | failed | 15.038s | ConnectTimeout: timed out |
| browser_like_headers | failed | 15.117s | ConnectTimeout: timed out |
| trust_env_false | failed | 15.040s | ConnectTimeout: timed out |
| no_redirects | failed | 15.040s | ConnectTimeout: timed out |

None of the variants reached HTTP response headers. Header changes, redirect behavior, and
`trust_env=False` therefore did not explain the failure.

## Diagnosis

Classification:

```text
server_intermittency
```

More precisely, this looks like intermittent VPS-to-BOCM TCP connectivity to:

```text
195.77.128.44:443
```

The evidence no longer supports the narrower hypothesis that `httpx` fails while `curl` succeeds.
During this task, `curl` also failed before connecting. The previous successful curl probe proves
the date and endpoint exist, but the connection is not reliable from the VPS at probe time.

## Code Changes

No code changes were made in this task.

Reason:

- the failure occurred before HTTP headers or redirects mattered;
- `curl_like_headers`, browser-like headers, `trust_env=False`, and no-redirect variants all failed;
- no production fallback to `curl` should be introduced;
- timeout remains correctly classified as `failed`, not `no_publication`.

## Smoke Result

No `ingest-bocm-date` smoke was rerun in this task.

Reason:

- the lower-level curl/httpx probes already reproduced the connection timeout;
- rerunning the CLI would only add another failed `ingestion_runs` row without new signal.

Post-diagnostic DB validation:

```text
status=valid
```

Safety counts remained:

```text
BOCM official_documents=982
BOCM PDF document_files=0
artifact_download_attempts=432
source_candidates=100
```

## Backfill Resume Decision

The BOCM 30-day metadata backfill should not resume yet.

Recommended next action:

```text
wait and retry a single 2026-05-06 search_day/ingest smoke from the VPS later
```

If the single-date smoke succeeds, resume from:

```text
2026-05-07 -> 2026-05-20
```

If it continues to fail, treat this as an external connectivity/source availability blocker and do
not start BOCM candidate dry-run.

## Known Limitations

- This diagnosis did not prove whether the failure is caused by BOCM-side filtering, upstream
  network routing, or transient service instability.
- No IPv6 path exists for `www.bocm.es` from the VPS probe.
- No broad retry loop was added.
- No candidates, PDFs, or downstream writes were created.

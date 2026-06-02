# Relay Provincial BOP Closeout

Date: 2026-06-01 / updated 2026-06-02

## Decision

`REL-001` is closed through the steamcases-vps IONOS relay.

The project now has validated metadata-only HTML monitors for the three provincial BOP sources that
were parseable but not reachable reliably from the project Hetzner VPS:

- `BOP_CUENCA`
- `BOP_SALAMANCA`
- `BOP_ZARAGOZA`

Current provincial BOP coverage is `43/43` monitor-validated entries.

## Relay Boundary

The relay is intentionally narrow:

- it accepts only `target=cuenca`, `target=salamanca`, or `target=zaragoza`;
- it accepts a `date` in `YYYY-MM-DD` format;
- it constructs official upstream URLs internally;
- it does not accept arbitrary URLs;
- it requires `X-Relay-Secret`;
- it is exposed through Caddy at `https://steamcases.desuscribir.es/official-sources-relay/api/fetch`;
- it returns either diagnostic JSON or raw upstream bytes with relay metadata headers;
- it performs no parsing, candidate creation, evidence generation, PDF download, or storage.

Relay files:

```text
deploy/steamcases/official-sources-fetch-relay/relay_server.py
deploy/steamcases/official-sources-fetch-relay/official-sources-fetch-relay.service
deploy/cloudflare/official-sources-fetch-relay/worker.js
deploy/vercel/official-sources-fetch-relay/api/fetch.js
```

Python monitor configuration:

```text
OFFICIAL_SOURCES_HTML_RELAY_BASE_URL=https://steamcases.desuscribir.es/official-sources-relay/api/fetch
OFFICIAL_SOURCES_HTML_RELAY_SECRET=<secret>
```

## Source Boundaries

All relay-backed monitor outputs remain metadata-only:

```text
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

No PDFs/artifacts are downloaded. No candidates, evidence-grade records, broad backfills, downstream
writes, or product automation are enabled by this task.

## Validation

Direct local and IONOS proof:

```text
local / BOP_CUENCA: HTTP 200
local / BOP_ZARAGOZA: HTTP 200
steamcases-vps / BOP_CUENCA: upstream_status=200 bytes=117758
steamcases-vps / BOP_SALAMANCA: upstream_status=200 bytes=82238
steamcases-vps / BOP_ZARAGOZA: upstream_status=200 bytes=139188
```

Project VPS proof through the steamcases relay:

```text
BOP_CUENCA: records=1, candidate_status=not_candidate, evidence_status=not_evidence
BOP_SALAMANCA: records=1, candidate_status=not_candidate, evidence_status=not_evidence
BOP_ZARAGOZA: records=1, candidate_status=not_candidate, evidence_status=not_evidence
```

Failed relay attempts remain documented as evidence of why the IONOS relay exists:

```text
Cloudflare Worker + Smart Placement:
  BOP_CUENCA: upstream_status=403
  BOP_SALAMANCA: upstream_status=522
  BOP_ZARAGOZA: upstream_status=522

Vercel:
  cdg1 / BOP_SALAMANCA: upstream_status=200 bytes=82238
  BOP_CUENCA: upstream_status=403 across tested regions
  BOP_ZARAGOZA: timeout across tested regions
```

Conclusion: Cuenca, Salamanca, and Zaragoza are operational through the steamcases-vps relay. Direct
project VPS fetch remains unreliable and must not be used as the health criterion for these three
sources.

# Opositar, Scrapling and BORM Access Review

Date: 2026-05-24

Scope: inspect whether `https://opositar.app/` and `D4Vinci/Scrapling` provide a safe path around the current BORM evidence blocker.

This is a report-only review. No VPS operation was run, no DB was touched, no candidates were created, and no artifacts were downloaded.

## Sources Inspected

Public web surface:

```text
https://opositar.app/
https://opositar.app/onboarding
https://opositar.app/robots.txt
https://opositar.app/sitemap.xml
```

Public repositories:

```text
https://github.com/D4Vinci/Scrapling
https://github.com/carm-es/BORM
```

Local clone snapshots:

```text
D4Vinci/Scrapling commit=ed008ef date=2026-05-18 subject="docs: updating a sponsor image"
carm-es/BORM commit=e66f503 date=2025-01-22 subject="Create README.md"
```

## Executive Result

Opositar does not prove that the BORM PDF evidence blocker has been solved.

The public surface supports a narrower interpretation:

```text
Opositar can plausibly operate as an alert/link product using metadata, public pages, official links, and email delivery.
It does not publicly demonstrate artifact-grade evidence download, raw hash preservation, review records, or BORM PDF access from a VPS.
```

Scrapling is technically relevant as a scraping framework, but not as a recommended fix for BORM evidence.

Reason:

```text
Scrapling explicitly includes stealth, proxy rotation, browser fingerprinting, and anti-bot bypass capabilities.
Those capabilities conflict with the current official-sources rule for BORM: do not bypass PerfDrive/Radware.
```

Recommended decision:

```text
Do not use Scrapling to bypass BORM PDF/HTML protection.
Keep BORM evidence paused unless an official non-PerfDrive evidence route is found.
Use Scrapling only as a possible parser/HTML-discovery reference for non-protected, low-risk sources.
```

## Opositar.app Findings

### Public stack

Observed headers for `https://opositar.app/`:

```text
server=Vercel
x-powered-by=Next.js
x-matched-path=/
cache-control=private, no-cache, no-store, max-age=0, must-revalidate
```

The content security policy includes analytics, MailerLite, and Stripe domains:

```text
connect.mailerlite.com
api.stripe.com
Google Analytics / Google Tag Manager
```

Assessment:

```text
This is consistent with a hosted Next.js product with onboarding, email capture, analytics, and future payment capability.
It does not reveal the ingestion pipeline.
```

### Public claims

The homepage claims:

```text
Vigilamos más de 60 boletines oficiales
BOE + 17 autonómicos + 50 provinciales
El BOE, los 17 boletines autonómicos y los 50 provinciales se revisan cada día laborable
Te llega un email el mismo día
Siempre con enlace directo a la publicación oficial
```

Assessment:

```text
These are product claims, not technical evidence of complete official-source ingestion.
They are compatible with metadata monitoring and official-link delivery.
They do not imply downloaded legal artifacts, PDF hashes, evidence review, or downstream-safe publication.
```

### Public crawl surface

`robots.txt`:

```text
User-Agent: *
Allow: /
Disallow: /panel/
Disallow: /api/
Disallow: /login

Sitemap: https://opositar.app/sitemap.xml
```

`sitemap.xml` lists only:

```text
https://opositar.app
https://opositar.app/onboarding
```

Assessment:

```text
There is no public searchable corpus or public API surface to inspect.
The `/api/` path is explicitly disallowed for crawlers, so it was not probed.
```

### Likely implementation model

Based only on public evidence, Opositar likely solves a different product problem:

```text
monitor official sources
classify notices for user preferences
send email alerts
link to official publication
```

That is not the same as the current `official-sources` evidence problem:

```text
download selected official artifact
store document_files
record artifact_download_attempts
hash raw bytes
support evidence review
avoid unofficial mirrors and anti-bot bypass
```

Conclusion:

```text
Opositar may be succeeding by not requiring artifact-grade evidence.
It is not evidence that BORM PDFs can be safely downloaded from our VPS.
```

## Scrapling Findings

Scrapling describes itself as an adaptive web scraping framework with:

```text
HTTP fetchers
dynamic browser fetchers
stealth browser fetchers
adaptive parsing
spiders/crawlers
session management
proxy rotation
MCP server
```

The README and docs explicitly advertise:

```text
anti-bot bypass
Cloudflare Turnstile / Interstitial handling
browser fingerprint impersonation
proxy rotation
stealthy_fetch MCP tools
bulk stealth fetches
```

Implementation indicators:

```text
Playwright dependency
browserforge dependency
apify-fingerprint-datapoints dependency
ProxyRotator
DynamicFetcher
StealthyFetcher
```

Assessment:

```text
Scrapling is stronger than BeautifulSoup/httpx for dynamic sites and brittle HTML.
It is also designed for exactly the class of behavior that official-sources should not use to defeat BORM PerfDrive/Radware protection.
```

Allowed future use, if any:

```text
local endpoint discovery for non-protected pages
HTML parsing experiments where normal official HTTP access succeeds
adaptive selector comparison against fixture HTML
one-off docs/local research with no DB writes and no artifacts
```

Disallowed for BORM evidence:

```text
stealth fetches against PerfDrive/Radware
rotating proxies
CAPTCHA/challenge solving
browser fingerprint spoofing
anti-bot bypass
unofficial mirrors
bulk crawling
```

## carm-es/BORM Cross-Check

The `carm-es/BORM` repository does not unblock BORM evidence.

Observed scope:

```text
artifactId=ActualizaFirmaWS
JAX-WS endpoint=/services/ActualizaFirmaWS
AFIRMA / RedSARA signature update integration
firmaCADES.xml
firmaPADES.xml
firmaXADES.xml
```

Assessment:

```text
This is a signature update service associated with BORM, not the public bulletin portal.
It does not expose a public metadata endpoint, HTML evidence endpoint, or alternative PDF delivery path.
```

## Decision for official-sources

Keep the current BORM decision:

```text
BORM metadata/candidates remain useful.
BORM evidence flow remains paused.
Do not run BORM evidence review with only 1/12 PDFs.
Do not attempt PerfDrive/Radware bypass.
```

Do not adopt Scrapling as a platform dependency now.

Reason:

```text
The immediate blocker is not parsing quality.
The blocker is official artifact access being redirected to a validation host from the VPS.
Adding a stealth scraping dependency would solve the wrong problem and weaken the audit posture.
```

## Recommended Next Tasks

Primary operational path:

```text
TASK-AUTO-BOA-003 — Controlled BOA 30-day metadata backfill
```

Parallel research path:

```text
TASK-AUTO-BORM-008D — Search for official non-PerfDrive BORM evidence endpoint
```

Rules for `BORM-008D`:

```text
official BORM/CARM endpoints only
no anti-bot bypass
no proxies
no challenge automation
no unofficial mirrors
no artifact downloads unless a clean official endpoint is found and scoped
```

Optional later experiment:

```text
TASK-RESEARCH-SCRAPLING-001 — Evaluate Scrapling parser only on local saved HTML fixtures
```

Rules:

```text
parser-only
no StealthyFetcher
no ProxyRotator
no live protected sites
no VPS
no DB
```


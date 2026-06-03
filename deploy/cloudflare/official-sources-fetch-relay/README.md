# official-sources fetch relay

Cloudflare Worker used only for provincial BOP endpoints that are parseable but not reachable
reliably from the project VPS.

Operational note: this Worker is not the currently validated runtime path. Local probes reached the
upstreams, but VPS-originated calls through Cloudflare still returned upstream `403/522` after Smart
Placement was enabled. The active runtime path is the steamcases-vps IONOS relay.

Allowed targets:

- `cuenca`
- `salamanca`
- `zaragoza`

The Worker does not accept arbitrary URLs. It receives `target` and `date`, builds the official
upstream URL internally, and returns either diagnostic JSON or raw upstream bytes with relay
metadata headers.

Example:

```bash
npx wrangler deploy
curl "https://official-sources-fetch-relay.<account>.workers.dev/?target=cuenca&date=2026-05-29"
curl "https://official-sources-fetch-relay.<account>.workers.dev/?target=cuenca&date=2026-05-29&raw=1"
```

The Python monitor can consume a relay through `OFFICIAL_SOURCES_HTML_RELAY_BASE_URL`, but the
validated production path currently uses the steamcases-vps IONOS relay.

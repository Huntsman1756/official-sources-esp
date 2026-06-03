# official-sources-fetch-relay

Vercel fallback relay for provincial BOP HTML monitors that are blocked from the
Hetzner VPS.

Operational note: Vercel `cdg1` validated `BOP_SALAMANCA`, but `BOP_CUENCA` still returned
upstream `403` and `BOP_ZARAGOZA` still timed out from tested Vercel regions. The active runtime
path is now the steamcases-vps IONOS relay for all three sources.

The endpoint is intentionally narrow:

- only `GET` is accepted;
- only `cuenca`, `salamanca`, and `zaragoza` targets are accepted;
- callers pass `date=YYYY-MM-DD`;
- upstream URLs are built internally;
- no arbitrary URL fetch is exposed.

Example:

```text
https://<deployment>/api/fetch?target=salamanca&date=2026-05-29&raw=1
```

Runtime wiring:

```powershell
$env:OFFICIAL_SOURCES_HTML_RELAY_BASE_URL = "https://<deployment>/api/fetch"
```

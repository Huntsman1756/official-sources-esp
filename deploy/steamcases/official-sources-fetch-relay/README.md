# official-sources-fetch-relay

Allowlisted relay for provincial BOP endpoints that are reachable from `steamcases-vps`
but not from the project Hetzner VPS.

Endpoint:

```text
GET https://steamcases.desuscribir.es/official-sources-relay/api/fetch?target=<cuenca|salamanca|zaragoza>&date=YYYY-MM-DD&raw=1
```

Security boundary:

- no arbitrary URL parameter;
- upstream URLs are built internally from target and date;
- `X-Relay-Secret` is required when `OFFICIAL_SOURCES_RELAY_SECRET` is set;
- TLS verification is disabled only for the allowlisted upstreams because their served chains fail
  on Ubuntu curl/OpenSSL even when the HTML is otherwise reachable.

Runtime:

```text
/opt/official-sources-fetch-relay/relay_server.py
/etc/systemd/system/official-sources-fetch-relay.service
Caddy route: /official-sources-relay/* -> 172.19.0.1:8017
UFW: 8017/tcp allowed from 172.19.0.0/16 and 157.90.22.40 only
```

from __future__ import annotations

import json
import os
import re
import ssl
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

TARGETS = {
    "cuenca": "https://www.dipucuenca.es/boletin-oficial-de-la-provincia",
    "salamanca": "https://sede.diputaciondesalamanca.gob.es/opencms/opencms/sede/BOP/index.jsp",
    "zaragoza": "https://boletin.dpz.es/BOPZ/",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def build_url(target: str, date: str) -> str:
    if target == "cuenca":
        year, month, day = date.split("-")
        params = urlencode(
            {
                "p_r_p_startDate": f"{day}/{month}/{year}",
                "p_r_p_endDate": f"{day}/{month}/{year}",
            }
        )
        return f"{TARGETS[target]}?{params}"
    if target == "salamanca":
        return f"{TARGETS[target]}?{urlencode({'fechaBoletin': date})}"
    return TARGETS[target]


class RelayHandler(BaseHTTPRequestHandler):
    server_version = "official-sources-fetch-relay/1.0"

    def do_GET(self) -> None:
        started = time.monotonic()
        secret = os.environ.get("OFFICIAL_SOURCES_RELAY_SECRET", "")
        if secret and self.headers.get("X-Relay-Secret") != secret:
            self._json({"error": "unauthorized"}, status=401)
            return

        parsed = urlparse(self.path)
        if parsed.path != "/api/fetch":
            self._json({"error": "not_found"}, status=404)
            return

        query = parse_qs(parsed.query)
        target = query.get("target", [""])[0]
        date = query.get("date", [""])[0]
        raw = query.get("raw", [""])[0] == "1"

        if target not in TARGETS:
            self._json({"error": "target_not_allowed", "allowed_targets": sorted(TARGETS)}, status=400)
            return
        if not DATE_RE.match(date):
            self._json({"error": "invalid_date", "expected": "YYYY-MM-DD"}, status=400)
            return

        upstream_url = build_url(target, date)
        status = 0
        headers: dict[str, str] = {}
        body = b""
        try:
            request = Request(
                upstream_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                    "User-Agent": "Mozilla/5.0 (compatible; official-sources-fetch-relay/1.0)",
                },
            )
            context = ssl._create_unverified_context()
            with urlopen(request, timeout=60, context=context) as response:
                status = response.status
                headers = {key.lower(): value for key, value in response.headers.items()}
                body = response.read()
        except HTTPError as exc:
            status = exc.code
            headers = {key.lower(): value for key, value in exc.headers.items()}
            body = exc.read()
        except (TimeoutError, URLError, OSError) as exc:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            self._json(
                {
                    "error": "upstream_fetch_failed",
                    "target": target,
                    "upstream_url": upstream_url,
                    "message": str(exc),
                    "elapsed_ms": elapsed_ms,
                },
                status=502,
                relay_headers=self._relay_headers(target, upstream_url, 0, 0, elapsed_ms),
            )
            return

        elapsed_ms = int((time.monotonic() - started) * 1000)
        relay_headers = self._relay_headers(target, upstream_url, status, len(body), elapsed_ms)
        if raw:
            self.send_response(status)
            self.send_header("Content-Type", headers.get("content-type", "text/html; charset=utf-8"))
            for key, value in relay_headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)
            return

        self._json(
            {
                "target": target,
                "upstream_status": status,
                "upstream_url": upstream_url,
                "upstream_bytes": len(body),
                "elapsed_ms": elapsed_ms,
            },
            status=200 if 200 <= status < 300 else 502,
            relay_headers=relay_headers,
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json(
        self,
        payload: dict,
        *,
        status: int = 200,
        relay_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (relay_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _relay_headers(
        target: str,
        upstream_url: str,
        upstream_status: int,
        upstream_bytes: int,
        elapsed_ms: int,
    ) -> dict[str, str]:
        return {
            "X-Relay-Target": target,
            "X-Relay-Upstream-Status": str(upstream_status),
            "X-Relay-Upstream-Url": upstream_url,
            "X-Relay-Upstream-Bytes": str(upstream_bytes),
            "X-Relay-Elapsed-Ms": str(elapsed_ms),
            "Cache-Control": "no-store",
        }


def main() -> None:
    host = os.environ.get("OFFICIAL_SOURCES_RELAY_HOST", "0.0.0.0")
    port = int(os.environ.get("OFFICIAL_SOURCES_RELAY_PORT", "8017"))
    ThreadingHTTPServer((host, port), RelayHandler).serve_forever()


if __name__ == "__main__":
    main()

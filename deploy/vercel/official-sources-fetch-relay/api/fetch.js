const https = require("node:https");

const TARGETS = {
  cuenca: {
    buildUrl(date) {
      const [year, month, day] = date.split("-");
      const formatted = `${day}/${month}/${year}`;
      const params = new URLSearchParams({
        p_r_p_startDate: formatted,
        p_r_p_endDate: formatted,
      });
      return `https://www.dipucuenca.es/boletin-oficial-de-la-provincia?${params.toString()}`;
    },
  },
  salamanca: {
    buildUrl(date) {
      const params = new URLSearchParams({ fechaBoletin: date });
      return `https://sede.diputaciondesalamanca.gob.es/opencms/opencms/sede/BOP/index.jsp?${params.toString()}`;
    },
  },
  zaragoza: {
    buildUrl() {
      return "https://boletin.dpz.es/BOPZ/";
    },
  },
};

function isValidDate(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function fetchUpstream(url, redirects = 0) {
  return new Promise((resolve, reject) => {
    const requestUrl = new URL(url);
    const request = https.request(
      requestUrl,
      {
        family: 4,
        rejectUnauthorized: false,
        timeout: 55_000,
        headers: {
          Accept:
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
          "User-Agent":
            "Mozilla/5.0 (compatible; official-sources-fetch-relay/1.0; +https://github.com/)",
        },
      },
      (upstream) => {
        const location = upstream.headers.location;
        if (
          location &&
          [301, 302, 303, 307, 308].includes(upstream.statusCode || 0) &&
          redirects < 5
        ) {
          upstream.resume();
          const redirectUrl = new URL(location, requestUrl).toString();
          fetchUpstream(redirectUrl, redirects + 1).then(resolve, reject);
          return;
        }

        const chunks = [];
        upstream.on("data", (chunk) => chunks.push(chunk));
        upstream.on("end", () => {
          resolve({
            body: Buffer.concat(chunks),
            headers: upstream.headers,
            status: upstream.statusCode || 0,
          });
        });
      },
    );

    request.on("timeout", () => request.destroy(new Error("upstream_timeout")));
    request.on("error", reject);
    request.end();
  });
}

function sendJson(response, payload, status = 200, headers = {}) {
  response.statusCode = status;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  for (const [key, value] of Object.entries(headers)) {
    response.setHeader(key, value);
  }
  response.end(JSON.stringify(payload, null, 2));
}

module.exports = async function handler(request, response) {
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    return sendJson(response, { error: "method_not_allowed" }, 405);
  }

  const requestUrl = new URL(request.url, "https://relay.local");
  const targetKey = requestUrl.searchParams.get("target") || "";
  const date = requestUrl.searchParams.get("date") || "";
  const target = TARGETS[targetKey];

  if (!target) {
    return sendJson(
      response,
      {
        error: "target_not_allowed",
        allowed_targets: Object.keys(TARGETS).sort(),
      },
      400,
    );
  }

  if (!isValidDate(date)) {
    return sendJson(
      response,
      { error: "invalid_date", expected: "YYYY-MM-DD" },
      400,
    );
  }

  const upstreamUrl = target.buildUrl(date);
  const startedAt = Date.now();
  let upstream;
  try {
    upstream = await fetchUpstream(upstreamUrl);
  } catch (error) {
    const elapsedMs = String(Date.now() - startedAt);
    return sendJson(
      response,
      {
        error: "upstream_fetch_failed",
        target: targetKey,
        upstream_url: upstreamUrl,
        message: error instanceof Error ? error.message : String(error),
        elapsed_ms: Number(elapsedMs),
      },
      502,
      {
        "X-Relay-Target": targetKey,
        "X-Relay-Upstream-Status": "0",
        "X-Relay-Upstream-Url": upstreamUrl,
        "X-Relay-Upstream-Bytes": "0",
        "X-Relay-Elapsed-Ms": elapsedMs,
        "Cache-Control": "no-store",
      },
    );
  }
  const body = upstream.body;
  const elapsedMs = String(Date.now() - startedAt);
  const relayHeaders = {
    "X-Relay-Target": targetKey,
    "X-Relay-Upstream-Status": String(upstream.status),
    "X-Relay-Upstream-Url": upstreamUrl,
    "X-Relay-Upstream-Bytes": String(body.length),
    "X-Relay-Elapsed-Ms": elapsedMs,
    "Cache-Control": "no-store",
  };

  if (requestUrl.searchParams.get("raw") === "1") {
    response.statusCode = upstream.status;
    for (const [key, value] of Object.entries(relayHeaders)) {
      response.setHeader(key, value);
    }
    response.setHeader(
      "Content-Type",
      upstream.headers["content-type"] || "text/html; charset=utf-8",
    );
    return response.end(body);
  }

  return sendJson(
    response,
    {
      target: targetKey,
      upstream_status: upstream.status,
      upstream_url: upstreamUrl,
      upstream_bytes: body.length,
      elapsed_ms: Number(elapsedMs),
    },
    upstream.status >= 200 && upstream.status < 300 ? 200 : 502,
    relayHeaders,
  );
};

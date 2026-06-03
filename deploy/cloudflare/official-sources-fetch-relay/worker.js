const TARGETS = {
  cuenca: {
    buildUrl(date) {
      const parsed = parseDate(date);
      const ddmmyyyy = `${parsed.dd}/${parsed.mm}/${parsed.yyyy}`;
      const url = new URL("https://www.dipucuenca.es/boletin-oficial-de-la-provincia");
      url.searchParams.set("p_r_p_startDate", ddmmyyyy);
      url.searchParams.set("p_r_p_endDate", ddmmyyyy);
      return url.toString();
    },
  },
  salamanca: {
    buildUrl(date) {
      parseDate(date);
      const url = new URL(
        "https://sede.diputaciondesalamanca.gob.es/opencms/opencms/sede/BOP/index.jsp",
      );
      url.searchParams.set("fechaBoletin", date);
      return url.toString();
    },
  },
  zaragoza: {
    buildUrl(date) {
      parseDate(date);
      return "https://boletin.dpz.es/BOPZ/";
    },
  },
};

const UPSTREAM_HEADERS = {
  "User-Agent": "Mozilla/5.0 official-sources-cloudflare-fetch-relay/0.1",
  Accept: "text/html,application/xhtml+xml",
  "Accept-Language": "es-ES,es;q=0.9",
};

export default {
  async fetch(request) {
    if (request.method !== "GET") {
      return Response.json({ error: "method_not_allowed" }, { status: 405 });
    }

    const requestUrl = new URL(request.url);
    const targetKey = requestUrl.searchParams.get("target") || "";
    const date = requestUrl.searchParams.get("date") || "";
    const target = TARGETS[targetKey];
    if (!target) {
      return Response.json(
        { error: "target_not_allowed", allowed: Object.keys(TARGETS) },
        { status: 400 },
      );
    }

    let upstreamUrl;
    try {
      upstreamUrl = target.buildUrl(date);
    } catch (error) {
      return Response.json({ error: "invalid_date", message: error.message }, { status: 400 });
    }

    const started = Date.now();
    const upstream = await fetch(upstreamUrl, {
      redirect: "follow",
      headers: UPSTREAM_HEADERS,
    });
    const body = await upstream.arrayBuffer();
    const elapsedMs = Date.now() - started;

    if (requestUrl.searchParams.get("raw") === "1") {
      const headers = relayHeaders({
        targetKey,
        upstream,
        bytes: body.byteLength,
        elapsedMs,
      });
      const contentType = upstream.headers.get("content-type");
      if (contentType) {
        headers.set("Content-Type", contentType);
      }
      return new Response(body, { status: upstream.status, headers });
    }

    return Response.json(
      {
        target: targetKey,
        upstream_status: upstream.status,
        upstream_url: upstream.url,
        bytes: body.byteLength,
        elapsed_ms: elapsedMs,
        content_type: upstream.headers.get("content-type"),
      },
      { headers: relayHeaders({ targetKey, upstream, bytes: body.byteLength, elapsedMs }) },
    );
  },
};

function relayHeaders({ targetKey, upstream, bytes, elapsedMs }) {
  return new Headers({
    "Cache-Control": "no-store",
    "X-Relay-Target": targetKey,
    "X-Relay-Upstream-Status": String(upstream.status),
    "X-Relay-Upstream-Url": upstream.url,
    "X-Relay-Upstream-Bytes": String(bytes),
    "X-Relay-Elapsed-Ms": String(elapsedMs),
  });
}

function parseDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    throw new Error("date must use YYYY-MM-DD");
  }
  const [, yyyy, mm, dd] = match;
  const parsed = new Date(`${yyyy}-${mm}-${dd}T00:00:00Z`);
  if (
    Number.isNaN(parsed.getTime()) ||
    parsed.getUTCFullYear() !== Number(yyyy) ||
    parsed.getUTCMonth() + 1 !== Number(mm) ||
    parsed.getUTCDate() !== Number(dd)
  ) {
    throw new Error("date must be a real calendar date");
  }
  return { yyyy, mm, dd };
}

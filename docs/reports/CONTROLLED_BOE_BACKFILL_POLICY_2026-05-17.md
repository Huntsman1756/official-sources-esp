# Controlled BOE backfill policy - 2026-05-17

## Summary

TASK-004C adds controlled BOE summary range ingestion, metadata-only candidate prefiltering,
structured cache-miss responses, and clearer status output. It does not implement a full BOE
historical archive download and does not add new source families.

## No-Publication Probe

The empirical probe tested:

- `2025-01-05`: Sunday, BOE returned `404` with a short XML body, mapped to `no_publication`.
- `2025-01-01`: national holiday, BOE returned valid JSON summary, not `no_publication`.
- `2024-12-24`: BOE returned valid JSON summary, not `no_publication`.
- `2024-12-31`: BOE returned valid JSON summary, not `no_publication`.

The code therefore keeps behavior based on observed response shape and HTTP status, not calendar
assumptions.

## Range Ingestion

New CLI:

```bash
official-sources ingest-boe-range --date-from YYYY-MM-DD --date-to YYYY-MM-DD
```

Range ingestion:

- is inclusive;
- validates both dates;
- rejects `date_from > date_to`;
- ingests summaries only;
- never downloads XML, HTML, or PDF artifacts;
- can skip existing `success` or `no_publication` dates;
- can continue through controlled `no_publication` dates;
- can stop on real failures.

## Safety Limits

- `--max-days` default: `90`.
- Ranges longer than `--max-days` fail.
- Ranges above `365` days require `--force`.
- Ranges above `365` days also require `--confirm-large-range`.
- No broad historical run is started automatically.

## Rate Limiting

The synchronous range runner reuses the existing BOE HTTP request policy with one shared client
and request limiter across the range. `--sleep-seconds` configures the limiter period. The
existing finite retry/backoff handling for 429, 503 and transient 5xx responses remains in use.

`aiolimiter` was not added because range ingestion is synchronous and uses the already-tested
internal limiter. No uncontrolled concurrency is introduced.

## Candidate Prefiltering

New CLI:

```bash
official-sources find-boe-candidates \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --keywords "beca,ayuda,subvencion,convocatoria"
```

The prefilter:

- searches locally stored BOE titles and metadata only;
- does not call BOE;
- does not download artifacts;
- does not parse full legal text;
- does not use LLMs;
- does not classify legal meaning;
- creates candidates with `review_status=human_review_required`;
- does not approve or publish anything.

Results can include false positives.

## Cache-Miss Behavior

Read-only paths return structured cache misses where practical:

```json
{
  "status": "cache_miss",
  "resource_type": "boe_summary",
  "date": "YYYY-MM-DD",
  "recommended_action": "Run controlled BOE ingestion for this date"
}
```

Cache misses do not trigger live fetching, arbitrary downloads, downstream writes, candidate
approval or publication.

## Status Output

`status --date` now separates summary and artifact HTTP state:

```text
summary_ingestion_status=success
summary_last_http_status=200
summary_retry_count=0
summary_throttle_triggered=0
artifact_http_status_summary=xml:200:114,html:200:114,pdf:200:114
artifact_retry_count=0
artifact_throttle_events=...
```

Legacy `ingestion_status` and `last_http_status` remain as aliases for summary status fields.

## Recommended First Backfill For la-ayuda / EduAyudas

Do not run this automatically without explicit approval.

Recommended policy:

1. Backfill BOE summaries for the last 24 months.
2. Identify candidates by keyword prefiltering.
3. Download XML/HTML only for candidates.
4. Download PDF only for human-accepted evidence or final citation evidence.

Before running it, require date count, request estimate, artifact policy, verified backup, and a
post-run report.

## Known Limitations

- No full historical archive automation was implemented.
- No downstream integration was implemented.
- Keyword matching is a first-pass metadata filter, not legal classification.
- Cache misses recommend operational actions but do not perform them.

# BOE no-publication probe - 2026-05-17

## Summary

An empirical probe was run against the BOE daily summary endpoint to verify how selected
non-publication-like dates behave before relying on `no_publication` in controlled range
ingestion.

Endpoint:

```text
/datosabiertos/api/boe/sumario/{fecha}
```

Each date was requested once. No artifacts were downloaded.

## Results

| Date | Reason | HTTP status | Content type | Body size | Body shape | Maps to `no_publication` |
| --- | --- | ---: | --- | ---: | --- | --- |
| 2025-01-05 | Sunday | 404 | application/xml | 170 bytes | XML/HTML body | yes |
| 2025-01-01 | national holiday | 200 | application/json | 84425 bytes | valid JSON summary with diary entries | no |
| 2024-12-24 | Christmas Eve | 200 | application/json | 372574 bytes | valid JSON summary with diary entries | no |
| 2024-12-31 | New Year's Eve | 200 | application/json | 343810 bytes | valid JSON summary with diary entries | no |

## Interpretation

- A Sunday probe returned BOE `404` with a short XML body. This matches the current
  `404 -> no_publication` behavior.
- The tested holiday-like dates were not no-publication days. BOE returned valid JSON summaries
  with diary entries.
- BOE publishes every day of the year except Sundays. National holidays, 24 December, and 31
  December can still have BOE publication.
- The implementation must not classify dates as `no_publication` based on a generic holiday
  calendar. `no_publication` applies to Sundays only unless empirical API evidence for a
  specific non-Sunday date proves otherwise and that date is explicitly allowlisted.
- BORME publication rules are different and must not be reused for BOE daily summary ingestion.

## Code Behavior

Current behavior remains correct for observed Sunday `404` responses. The implementation also
supports controlled no-publication detection for Sunday empty responses, Sunday JSON summaries
without diary entries and without metadata, and Sunday XML/HTML error-like no-document bodies.

Non-Sunday valid summaries are stored as `success`. Non-Sunday `404`, API, network, parser, and
storage failures are stored as `failed` unless the exact date has been explicitly allowlisted
from observed BOE behavior.

Malformed JSON `200` responses still fail as real parser failures.

## Limitations

- This is a small probe, not a formal BOE publication calendar.
- BOE response behavior can change; range ingestion must continue to persist actual HTTP status
  and clear audit fields.
- Raw response bodies were not stored in this report.

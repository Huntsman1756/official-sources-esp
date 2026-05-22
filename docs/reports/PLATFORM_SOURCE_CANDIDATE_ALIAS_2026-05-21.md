# Platform Source Candidate Alias - 2026-05-21

## Summary

`official-sources find-source-candidates` is the preferred generic command for source candidate
prefiltering. It uses the same local metadata matching path as the existing
`official-sources find-boe-candidates` command.

The legacy command remains available as the backwards-compatible BOE-default/source-aware entry
point.

## Supported Sources

The generic alias accepts:

- `BOE`
- `BOJA`
- `DOGV`
- `BOCM`
- `BDNS`

All sources use stored `official_documents` metadata. The command does not call live source APIs
or download artifacts.

## Write Safety

Dry-run mode is available with `--dry-run` or `--no-write` and does not create
`source_candidates`.

Write mode requires explicit `--write`. In write mode, `--limit` caps candidate creation count.
In dry-run mode, `--limit` caps printed samples only.

## Compatibility

`find-boe-candidates` keeps the BOE default and accepts the same source-aware options. Existing
BOE runbooks do not need to change immediately, but new source-family docs should prefer
`find-source-candidates`.

## Validation Scope

The platform tests cover:

- alias help availability and preferred-command text;
- shared logic for BOJA through the new alias;
- BOE default compatibility through the legacy command;
- dry-run behavior for DOGV, BOCM, and BDNS local metadata;
- explicit `--write` requirement before candidate creation;
- dry-run and `--no-write` no-write guarantees.

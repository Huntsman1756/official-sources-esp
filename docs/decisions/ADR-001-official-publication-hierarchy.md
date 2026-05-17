# ADR-001: Official Publication Hierarchy

## Status

Accepted.

## Context

`official-sources` is not merely a BOE wrapper. It is intended to be a reusable official-publication infrastructure layer for ingesting, tracing, citing, and auditing public official sources.

The first implemented source family is the Spanish state-level BOE. Future source families must not be blurred into BOE terminology or forced into a single parser model.

## Official Publication Hierarchy

`official-sources` distinguishes between:

1. State official source:
   - BOE.

2. Autonomous/statutory territory official sources:
   - 17 autonomous community official journals.
   - Ceuta and Melilla official bulletins.

3. Provincial/local official sources:
   - Provincial official bulletins.
   - Municipal official gazettes only where required.

4. European Union official sources:
   - Official Journal of the European Union via EUR-Lex/CELLAR.
   - TED/OJ S as a separate future procurement source.

## Decision

The project adopts these architecture invariants:

- Do not use the term `autonomous BOE`.
- BOE is a state-level source, not a generic synonym for official bulletins.
- Autonomous/statutory territory bulletins must be modeled as independent source adapters.
- Ceuta and Melilla must not be forced into the same model as ordinary autonomous communities without an explicit note.
- Provincial and municipal sources are future heterogeneous adapters, not one generic parser.
- EUR-Lex/DOUE must be treated as a separate EU source family.
- TED/OJ S must be treated as a future procurement-specific adapter, separate from normative EU law.
- Tier 1 remains the only implemented tier for now.
- Future tiers must not be implemented until explicitly scheduled in the roadmap.

## Consequences

Current implementation scope remains Tier 1 only:

- BOE daily publications.
- BOE controlled XML/HTML/PDF artifacts.
- BOE consolidated legislation.
- BOE consolidated index and block retrieval.

Future adapters must each define their own:

- source policy;
- endpoint policy;
- schema needs;
- ingestion audit behavior;
- integrity behavior;
- citation behavior;
- tests and fixtures.

The project must keep read-only MCP behavior separate from operational ingestion and migration commands. It must not publish, approve, interpret legal obligations, or write into downstream projects.

# ADR-0001: Modular monorepo

- Status: accepted
- Date: 2026-08-25

## Context

The registry, UI, computation services, migrations, and infrastructure evolve
together and need shared documentation and CI.

## Decision

Use a monorepo containing a modular FastAPI application, Next.js web app, Python
worker, shared types, data tooling, and infrastructure. Keep dependency boundaries
explicit and allow services to split only when operational needs justify it.

## Alternatives

Separate repositories increase coordination and version skew. A single unstructured
application would obscure scientific and inventory boundaries.

## Consequences

Cross-component changes are atomic and easier for maintainers; CI must selectively
validate multiple ecosystems and module ownership must be documented.

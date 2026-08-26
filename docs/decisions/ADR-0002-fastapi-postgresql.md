# ADR-0002: FastAPI and PostgreSQL source of truth

- Status: accepted
- Date: 2026-08-25

## Context

The system needs relational integrity, flexible scientific integrations, migrations,
and a typed HTTP interface.

## Decision

Use Python/FastAPI, SQLAlchemy 2, Alembic, and PostgreSQL. Route handlers delegate
to services/repositories. Core concepts are relational; JSONB is reserved for truly
dynamic metadata and provenance parameters.

## Alternatives

Django offers a mature admin but would not remove the need for explicit domain
services. A document database weakens the central relational and constraint model.

## Consequences

Python scientific integration is direct and schema evolution explicit. PostgreSQL-
specific behavior requires containerized integration tests in addition to unit tests.

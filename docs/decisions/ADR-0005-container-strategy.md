# ADR-0005: Compose with Micromamba Python images

- Status: accepted
- Date: 2026-08-25

## Context

Development and deployment must reproduce Python/scientific dependencies and run on
institutional infrastructure.

## Decision

Use Docker Compose initially, Micromamba-based API/worker images synchronized with
Conda environment files, a normal Node/pnpm web image, and separate internal/public
networks. Caddy is the single production ingress.

## Alternatives

Host-only environments drift. Putting Node in Conda adds little value. Kubernetes
is premature without an institutional target.

## Consequences

Developers get one stack command and reproducible Python tools. Image builds are
larger than minimal wheels and CI must verify environment/container consistency.

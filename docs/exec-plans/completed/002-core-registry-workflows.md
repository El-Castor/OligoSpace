# Execution plan 002: Core registry workflows

- Status: completed
- Started: 2026-08-26
- Completed: 2026-08-26

## Objective

Turn the read-only foundation into a usable registry: a researcher must be able to
search, create, inspect, and update oligos, targets, and assays through the web UI,
while the API preserves visibility, authorization, scientific identity, and audit
provenance.

## Affected components

- Caddy ingress and the NextAuth route boundary.
- FastAPI registry routes, schemas, services, and repositories.
- Next.js registry lists, global search, create/detail/edit pages, and forms.
- PostgreSQL-backed route and authorization integration tests.
- Developer documentation and current project state.

## Data migrations

No schema migration is planned for the first increment. Existing stable public IDs,
visibility fields, record statuses, assay versions, and audit events are used. Any
new persistence requirement discovered during implementation must receive a
reversible Alembic revision before it is used.

## API and UI changes

- Restrict the public API proxy match to `/api/v1/*` so `/api/auth/*` remains owned
  by Next.js, and install the missing NextAuth route handler.
- Add visible search, public-ID detail reads, and authorized metadata updates for
  oligos, targets, and assays.
- Keep oligo sequence immutable after creation; changing biological identity means
  registering a new oligo rather than silently rewriting calculated provenance.
- Provide accessible search, creation, detail, and edit workflows for the three
  core registries, including explicit API failure and empty states.
- Make global search operational across oligos, targets, and assays.

## Tests

- Unit tests for update contracts, search normalization, and authorization helpers.
- PostgreSQL integration coverage for create/search/read/update, audit events,
  duplicate rejection, and forbidden edits.
- Web lint, strict type checking, component/helper tests, and production build.
- Playwright E2E through Caddy for root, development authentication, dashboard,
  oligo list/create/detail/edit, target create/detail, assay create with forward and
  reverse roles, global search, and reload persistence.
- Persistence acceptance MUST traverse the full chain: UI create → API → PostgreSQL
  → browser reload → the same stable public record remains available.

## Risks

- OIDC and development bypass follow different request paths; both ingress routes
  must remain valid.
- Updates could accidentally rewrite sequence identity or bypass visibility checks.
- Assay association replacement must validate roles and accessible oligos before
  changing an existing design.
- Local image rebuilds can mask stale-container behavior if live smoke tests do not
  rebuild both API and web images.

## Completion criteria

- The documented application URL renders the web workspace through Caddy.
- All three core registries support search, create, detail, and authorized edit.
- Mutations create audit records and oligo sequence identity cannot be overwritten.
- PostgreSQL integration tests and all required repository checks pass.
- Status, backlog, changelog, and operator instructions reflect the delivered state.

## Progress

- Plan activated from the ordered `Now` backlog on 2026-08-26.
- Ingress/auth routing defect identified before implementing registry workflows.
- Core search/create/detail/edit API and web source implemented for oligos, targets,
  and assays.
- Isolated PostgreSQL route integration passes create/search/read/update, duplicate
  and immutable-sequence rejection, audit/version checks, and forbidden edits.
- Canonical requirements catalogue and traceability matrix added; project status now
  distinguishes build, service runtime, and browser workflow verification.
- Production web/API images and the core Compose path start behind Caddy.
- Playwright Chromium passes the complete development journey through Caddy,
  including dashboard, development identity, all three core registries, contextual
  oligo roles, global search, and persistence after reload.
- Required format, lint, type-check, unit/web/worker, PostgreSQL integration, and
  Playwright suites pass on 2026-08-26.

## Outcome

The earlier browser 404 was traced to an over-broad Caddy API matcher, stale
container DNS resolution, and the standalone Next.js bind address. Those boundaries
are corrected. A researcher can now create, find, inspect, and edit oligos, targets,
and assays through the browser while the API enforces visibility and immutable
oligo sequence identity, writes audit events, versions assay edits, and persists the
records in PostgreSQL across browser reloads. Later product phases remain inactive.

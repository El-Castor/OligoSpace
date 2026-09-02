# Execution plan 003: Identity, users, workspaces, and administration

- Status: completed
- Started: 2026-08-26
- Completed: 2026-09-02

## Objective

Make OligoSpace genuinely multi-user. An authenticated person must have a projected
application profile, role-aware teams and projects, personalized workspace data,
and server-authorized administration. Development authentication must exercise real
PostgreSQL users without introducing application-managed passwords; production
authentication remains Keycloak OIDC.

## Requirements in scope

- `AUTH-001` through `AUTH-005`.
- `USER-001` through `USER-003`.
- `TEAM-001` through `TEAM-003`.
- `PROJECT-001` through `PROJECT-004`.
- Collaboration portions of `SEARCH-001`, `SEARCH-003`, `AUDIT-001`, and
  `AUDIT-002`.
- Administrative catalogue workflows in `ORGANISM-001`, `EXPTYPE-001`, and
  `EXPTYPE-003`.

Requirements whose acceptance depends on ExperimentRun, Validation, attachments,
inventory, or later scientific phases remain Planned or In progress; this plan MUST
not manufacture those data merely to complete a dashboard.

## Existing capabilities to preserve

- Plan 002 Caddy ingress and the browser-verified oligo, target, assay, contextual
  role, global-search, audit, and persistence workflows.
- FastAPI/SQLAlchemy/Alembic boundaries and PostgreSQL as source of truth.
- Keycloak OIDC architecture and the production prohibition on development auth.
- Primer3/BLAST worker and Docker/Micromamba architecture.

## Data model and migrations

- Extend `User` with identity-provider metadata, optional first/last names, and a
  last-login timestamp while retaining immutable internal ID and OIDC subject.
- Add explicit Project visibility and preserve stable public IDs, creator, status,
  optional owning team, and memberships.
- Keep team and project membership roles relational and auditable.
- Add a reversible Alembic revision with PostgreSQL indexes/constraints and
  deterministic local seed updates for an administrator and a normal researcher.
- PostgreSQL RLS is not introduced in this plan: ADR/data-model guidance requires
  stabilized application-policy integration tests first, and the current connection
  model has no safe per-request DB security context. This remains defense-in-depth
  hardening, not a substitute for API authorization.

## Backend and authorization

- Load the real projected user and membership roles in both OIDC and development
  authentication contexts; reject inactive users.
- Make development login explicit and session-backed. Server-to-server development
  identity projection MUST be integrity-protected and unavailable in production.
- Complete profile, team, membership, project, project-membership, dashboard, user
  administration, ExperimentType, and organism APIs.
- Validate Team/Project ownership assignments and Private/Project/Team/Institute
  visibility on every affected core-registry mutation.
- Audit user activation/role changes, memberships, projects, teams, catalogues, and
  visibility changes without recording credentials, cookies, tokens, or secrets.

## Frontend

- Replace the static initials circle with an accessible user menu containing
  identity, profile, team context, and logout.
- Provide explicit development login and retained Keycloak login for OIDC mode.
- Add usable profile, team list/detail/member management, project
  list/create/detail/edit/member management, and admin pages.
- Admin covers user projection/search/status/role, teams, projects,
  ExperimentTypes, and organism controlled vocabulary.
- Personalize the dashboard with real current-user, project, team-shared, recent
  record, and recent activity data; later-domain facts remain explicit unavailable
  states.
- Extend core resource forms with accessible Team/Project scope choices.

## Tests

- Unit tests: authentication claims/runtime guards, permission helpers, membership
  roles, visibility assignment, and schema contracts.
- PostgreSQL integration: real users, inactive rejection, team/project membership,
  Private/Team/Project/Institute visibility, admin/member forbidden boundaries,
  project persistence, catalogue administration, and audit events.
- Split Playwright by concern (`smoke`, `auth`, core registries, `workspaces`, and
  `admin`) rather than retaining one monolithic journey.
- Browser E2E through Caddy: development login, profile, personalized dashboard,
  project create/reload, Team page, admin access, normal-user forbidden admin
  operation, logout, cleared session, and successful return login.
- Final host smoke test MUST use `http://oligospace.localhost:8080`; the internal
  Docker browser journey alone is insufficient.

## Risks

- Development impersonation must never become a production authentication path.
- Keycloak access-token refresh and application account disablement have distinct
  lifecycles and must fail closed.
- Membership edits can grant access to previously hidden scientific records; every
  change requires server authorization and audit evidence.
- Existing records may have Team visibility without an owning team. The UI must
  make new assignments explicit without silently rewriting historical records.
- Browser scenarios must use clearly labeled E2E data and remain isolated enough
  to run repeatedly against a persistent development database.

## Completion criteria

- Development login/logout and OIDC session lifecycle configuration are implemented;
  production still rejects development auth and insecure session defaults.
- User profile, teams, projects, membership roles, administration, and personalized
  dashboard are usable through Caddy and persisted in PostgreSQL.
- Private, Team, Project, and Institute visibility boundaries pass explicit API and
  PostgreSQL tests; a normal user cannot perform admin operations.
- Project create → API → PostgreSQL → browser reload persistence passes.
- Required format, lint, typecheck, unit, PostgreSQL, split Playwright, production
  image build, Compose validation, and host-browser smoke tests pass.
- STATUS, BACKLOG, CHANGELOG, traceability, and this plan record exact evidence. Only
  then may the plan move to `completed/`; no plan 004 is activated automatically.

## Progress

- Plan activated after plans 001 and 002 were completed and browser-verified.
- Documentation, ADRs, repository state, existing schema, auth boundary, permission
  policy, placeholders, and current tests inspected before implementation.
- Confirmed that User/Team/Project tables are partial foundations, not completed
  workflows, and that plan 002 functionality can be extended without restructuring.
- Added reversible migration `0002_identity_workspaces`, expanded projected users,
  Project visibility/update provenance, membership indexes, and deterministic local
  administrator/researcher identities.
- Replaced implicit development administration with explicit NextAuth identities and
  HMAC-protected server projection; OIDC refresh/logout configuration and inactive-user
  rejection remain fail-closed.
- Implemented profile, Team, Project, membership, dashboard, user administration,
  ExperimentType, and organism APIs with audit events and server-side authorization.
- Implemented browser login/logout, profile, personalized dashboard, Team and Project
  workflows, administration, workspace selectors on core forms, and Project search.
- Split the monolithic browser journey into six concern-specific Playwright specs.
- Corrected E2E networking so Chromium uses the public `oligospace.localhost` origin
  and cookie domain while sharing Caddy's network namespace.
- Made PostgreSQL integration execution idempotent by removing stale ephemeral test
  containers before and after every run.

## Outcome

- Build verified: `make format`, `make lint`, `make typecheck`, and `make test` passed
  through the container toolchain on 2026-09-02; this includes 19 API unit tests, 2
  real Primer3 worker tests, web tests, strict Python/TypeScript checks, and successful
  production API/web image builds. Primer3 compiled and BLAST+ 2.17.0 passed checksum.
- API/PostgreSQL verified: `make test-integration` applied `0001` and `0002` to a fresh
  PostgreSQL 17 instance and passed 3 integration tests covering the preserved core
  registry plus identity, memberships, four visibility scopes, disabled accounts,
  authorization boundaries, persistence, and audit events.
- Browser/E2E verified: `make test-e2e` passed 6 Chromium specs through Caddy. A
  separate host-network Chromium smoke passed against
  `http://oligospace.localhost:8080`, and host HTTP smoke verified root redirect,
  login page, and health response.
- Production institutional OIDC remains implemented but not browser-qualified because
  institutional inputs are unavailable. Later scientific, evidence, inventory, and
  backup phases remain explicitly outside this plan.
- No plan 004 or later plan was activated automatically.

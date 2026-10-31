# UI component inventory and migration strategy

2026-10-31. Inventory limited to the frontend touched by the requested prototype;
this is not a general OligoSpace audit. No production migration is performed.

## Existing implementation

Next.js 16.3.3 / React 19.2.8 / TypeScript 5.9.2; existing CSS and native controls.
Tailwind is installed, but the current UI uses `app/globals.css`. No shadcn,
component or icon library is installed. Preserve NextAuth and server-component /
server-action boundaries. No dependency addition is required for this prototype.

| Existing component | Current responsibility | Proposed visual migration |
|---|---|---|
| AppShell, UserMenu | Navigation, current identity, logout | Rail/header geometry and tokens; retain identity/auth logic |
| PageHeader, RecordDetails, RecordField | Hierarchy and record facts | Type scale, spacing, semantic field presentation |
| RegistryTable, RegistrySearch | Listing and GET search | Flat dense table, labeled scroll region, responsive filter layout |
| OligoForm, TargetForm, AssayForm | Scientific forms bound to server actions | Field/button tokens, grouping and errors; unchanged names/payloads/actions |
| WorkspaceFields, ProjectForm | Scope/membership-dependent fields | Visual grouping only; no policy duplication |
| ExperimentRunForm, ValidationForm | Experimental evidence | Same form primitives; retain evidence/provenance labels |
| Primer3JobSection, ScientificJobAutoRefresh | Submit/poll/read persisted jobs | Calm progress/history rows; preserve real provenance, failure and stale-version behavior |
| AttachmentUploadForm, AttachmentList | Quarantine/evidence | Preserve upcoming R1-06 policy and quarantine states |
| LoginActions, profile/admin/team pages | Identity and administration | Migrate last behind auth/permission regression coverage |
| PlannedPage | Explicit unavailable features | Readable empty state; do not imply implementation |

## Why the demo is a separate Next.js root

The production root layout imports AppShell, which requests `/me`, and proxy.ts
requires a session. Putting a public demo inside that root would require auth/shell
exceptions or a backend. The isolated root `apps/web/prototype` uses the parent's
installed Next/React packages while having its own layout, CSS, route and build
output. The ordinary production app does not route to it. The demo root also
returns 404 outside `NODE_ENV=development`. No production route, shared component
or auth rule is modified.

## Local access

From `apps/web`, with the existing dependencies installed:

```sh
npm exec -- next dev prototype --hostname 127.0.0.1 --port 3100
```

Open `http://127.0.0.1:3100`. No login, backend or database is required. Do not use
`next start` for the demo: production mode deliberately returns 404. The first
implementation run can also use the repository's existing Docker tooling image;
the final handoff records the exact local runtime used.

Current local runtime: container `oligospace-soft-ui-prototype`, using existing
image `oligospace-web-tooling`, binding only `127.0.0.1:3100`. From the repo root:

```sh
rtk docker run --detach --rm --name oligospace-soft-ui-prototype \
  --publish 127.0.0.1:3100:3100 \
  --volume "$PWD/apps/web/prototype:/app/prototype" --workdir /app \
  oligospace-web-tooling npm exec -- next dev prototype --hostname 0.0.0.0 --port 3100
```

Stop with `rtk docker stop oligospace-soft-ui-prototype` before switching to a
branch without the prototype. This is a local development process, not hosting.

## Migration controls

Approval applies to the prototype only. Before migrating: agree on the reviewed
screenshots and tokens, baseline current E2E/screens, introduce scoped primitives,
then replace styling one surface at a time. Keep each PR reversible and run the
relevant permission/lifecycle/provenance tests. Do not replace a real scientific
state with a mock. Design validation does not authorize a merge of this branch.

Functional R1-06 and R1-07 remain next on main. Their upload policy and CSV behavior
must be established independently, then reflected in any later visual migration.

## Execution evidence

Reference iteration validated before applying the user's subsequent adjustments:
parent Next build and prototype Next build passed; prototype production mode
returned HTTP 404; three Chromium tests passed (desktop/local interactions, copy,
density, mobile/keyboard/reduced motion, tested AA contrast pairs). Seven reference
captures are retained under `evidence/baseline/`. Existing lint/typecheck/unit
checks passed (API 35, worker 14, web 2; PostgreSQL cases skipped in unit-only run).

The first browser run exposed Next dev-origin blocking, corrected only in the
prototype config for 127.0.0.1. Browser test locators were then scoped to avoid
Next's route-announcer alert and clarify the status select's accessible name.
The integrated Browser execution tool was unavailable, so existing Playwright
Chromium was used, with actual screenshots inspected.

Iteration 02 reinforces elevation, lightens/nuances the sidebar, uses synthetic
plant examples and smaller compact rows. Three Chromium tests cover clipboard
contents, species filtering, local insertion/reset, states, keyboard, reduced
motion and sampled contrast. Layout checks use 320/390/768/1024 px, with desktop
at 1440 px. Captures preserve the reference separately:

- [Reference desktop](evidence/baseline/01-desktop.png)
- [Revised desktop](evidence/iteration-02/01-desktop.png)
- [Compact](evidence/iteration-02/02-compact.png)
- [Mobile](evidence/iteration-02/07-mobile.png)
- [Loading](evidence/iteration-02/04-loading.png),
  [error](evidence/iteration-02/05-error.png),
  [empty](evidence/iteration-02/06-empty.png)

Final format/lint/typecheck and API/worker/web unit checks pass (35/14/2).
The unit-only run skips 193 PostgreSQL cases; no database implementation changed.
All 15 existing application Chromium tests pass in the isolated E2E environment,
which was removed afterward. Prototype and existing application builds pass;
the latter exposes no prototype route. Scoped independent review found no
blocking or important issue. Limits: Chromium only, sampled contrast rather than
WCAG certification, no screen-reader or real-device qualification. Dark theme
remains a specification.

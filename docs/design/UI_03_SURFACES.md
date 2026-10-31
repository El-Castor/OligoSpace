# UI-03 — production cards, panels and surfaces

2026-10-31. User-authorized surfaces lot after validated UI-02. Base main
`5598ebd` (PR #11, commits `4558ce1`/`952f390`, 12 successful PR/push checks
confirmed before starting). UI-04/05/06 are not started.

## Implementation and boundaries

Production changes only `design-tokens.css` and `globals.css`. A dedicated
`--shadow-panel` moderately strengthens paired light/dark elevation without
changing UI-02 navigation/menu shadows. Shared dashboard, form, record detail,
provenance/association, workspace, search and administrative outer surfaces use
the same token and existing blue-gray surface palette. Outer radii use the
existing major-radius token; dense tables remain tables with unchanged rows.

Dashboard panels align at their start, keeping independent content-driven
heights instead of stretching to the taller sibling. Statistics use available
desktop width for the same five existing metrics, retain tabular numerals and
separate labels, values and descriptions. No metric, backend field, fallback,
scientific calculation or copy is added or changed. Secondary metadata is 13 px
with explicit line height and existing accessible text colors. Record fields
and workspace cards lose artificial minimum heights without hiding information.

There is no React component, prop, input, server action, auth/session, API,
permission or schema change; no dependency. Shared empty/error presentations
retain their actual messages and behavior. Existing Primer3 jobs/loading flows
remain covered by their functional journeys; no simulated loading screen is
introduced. UI-02 shell/links/role menus remain intact.

## Comparable real-route evidence

External captures: `/private/tmp/oligospace-ui03/{before,after}/`, using a fresh
isolated API/PostgreSQL-backed E2E stack on each run, with identical 1440×1000
desktop viewport and identical input specimens/sequences/IDs/counts. No route
responses or application state are mocked. Fixture data never enters production
code or a development/pilot database. Timestamps naturally differ between runs.

- `dashboard-empty.png`: initial viewer, zero resources/activity.
- `dashboard-sparse.png`: admin after one actual Oligo creation, one item/event.
- `dashboard-full.png`: eleven actual Oligos, five recent resources of that type
  under the existing backend per-type limit, eight displayed audit events.
- `record-details.png`, `record-form.png`, `record-error.png`: same Oligo detail,
  real form and actual invalid-sequence server feedback.
- `dashboard-mobile.png`: same populated scenario at 390×1000; overflow checks
  additionally exercise 320, 768 and 1024 px. Existing shell checks include1440px.

Baseline uses exact main styles before UI-03. The initial Docker-registry DNS
failure was transient; the subsequent baseline and final builds/tests succeeded
without network configuration changes. New fixture assertions were aligned to
the observed and source-confirmed five-per-type backend contract, not by altering
the backend to match a visual expectation.

The new test verifies both populated panels end at their actual last child's
bottom and differ in height, and measures text contrast >=4.5:1 and metadata
size >=13 px. Real production screenshots were inspected against the baseline
and the approved prototype. Integrated browser tooling remains unavailable;
existing Playwright Chromium was used without installation.

## Validation and residual differences

Final browser suite: 23 passed, no skips; PostgreSQL:198 passed with migration
round-trip. Existing role, session, navigation keyboard/modal, permissions,
lifecycle, Primer3 persistence, upload policy and CSV journeys stay green.
Format/lint/typecheck, production builds and 52 API/14 worker/2 web unit gates
are required before delivery; the PR records exact final CI results.
Independent scoped review found no important issue.

The prototype's panel palette/elevation and hierarchy are carried into real
surfaces, while production keeps all original metrics, provenance and workflow
content. Compact tables, copy controls, inner domain form/job redesign and dark
theme remain later lots. Blank space beneath a shorter panel is normal grid
space, not empty height inside that panel. No reader/real-device/full-WCAG or
institutional OIDC certification is claimed.

The new density scenario requires the existing serial suite against a fresh E2E
database; it is not suitable for parallel tests sharing accumulated data. Revert
UI-03's two style/token files together to roll back appearance; no data rollback.
User images in `assests/` remain untouched and excluded. Stop after this lot's
green-CI merge and report; no later graphical lot begins here.

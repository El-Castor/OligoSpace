# Scientific Soft UI — preparation for shared-component integration

2026-10-31. Preparation only, after functional R1-06/R1-07. No production
component, authentication flow or scientific workflow is changed by this document.

## Official reference

The user approved iteration 02 as the official visual reference. Preserve branch
`codex/scientific-soft-ui-prototype` at
`1aeec1a2135d006d700286a506242d2a51142c99`, without merging it.

Canonical reference files at that exact commit:

- [Design system](https://github.com/El-Castor/OligoSpace/blob/1aeec1a2135d006d700286a506242d2a51142c99/docs/design/SCIENTIFIC_SOFT_UI_DESIGN_SYSTEM.md)
- [Component inventory and evidence](https://github.com/El-Castor/OligoSpace/blob/1aeec1a2135d006d700286a506242d2a51142c99/docs/design/UI_COMPONENT_MIGRATION.md)
- [Previously requested visual estimate](https://github.com/El-Castor/OligoSpace/blob/1aeec1a2135d006d700286a506242d2a51142c99/docs/design/UI_REDESIGN_ROADMAP.md)
- `apps/web/prototype/app/tokens.css`, `prototype.css`, `components/Icon.tsx`
  and the reference/iteration-02 screenshots in `docs/design/evidence/`.

The mock dashboard, local insertion, static job progress and fake profile are
visual specimens. They must never replace production data, actions or identity.
Port selected presentation primitives; do not cherry-pick the prototype app root,
its development guard, routing/configuration or fictional state into production.

## Proposed independent, reversible PR boundaries

This refines the existing visual proposal; it does not create a new functional
roadmap or authorize a global rewrite. Each PR must be reviewable on its own.

| PR | Shared seam | Acceptance and rollback |
|---|---|---|
| 1 — tokens and primitives | Scoped semantic tokens, panel/button/field styles, existing outline icon language | Baseline production screenshots first; preserve defaults until explicitly adopted. Check text/borders/focus contrasts. Revert isolated token/style additions. |
| 2 — shell and hierarchy | AppShell, UserMenu, PageHeader | Apply rail/header/spacing; keep `/me`, identity display, session handling and logout implementation intact. Keyboard/mobile screenshots and auth E2E. Revert presentation commit. |
| 3 — registry table and search | RegistryTable, RegistrySearch, small client-only sequence-copy/density controls | Preserve server children/count/columns interface and GET `q`; semantic headers, confined horizontal scroll, real comfortable/compact density. Preserve R1-07 CSV link and current query. Revert component presentation without endpoint changes. |
| 4 — record fields and forms | RecordDetails, RecordField, shared field/button presentation used by Oligo/Target/Assay forms | Preserve input names, payload normalization, bound server actions, validation/errors and scope choices. Keyboard/error states plus lifecycle and role tests. Revert styling only. |
| 5 — scientific/evidence panels | Primer3JobSection and evidence forms/lists | Keep live polling, stale-version/failure states, algorithm/parameter/reference/time provenance, validation context and history. Preserve R1-06 disabled notice and old quarantine records. Never substitute mock progress. |
| 6 — remaining administration | Workspace/profile/catalogue/identity presentation | Retain server-side authorization and existing mutations. Cross-role, mobile, keyboard and session regressions before review. |

The first implementation candidate is PR 1 only. Settle its scope from the
approved token specimen and production screenshots; no new UI dependency is
needed. Dark theme remains a separately qualified follow-up, not an untested
toggle. Future primitives should compose native/server-rendered components;
clipboard/density are small client islands, not a client rewrite of scientific forms.

## Functional invariants and gates

- Backend authorization remains authoritative. Keep all user/team/project/
  organization restrictions, lookup errors and non-leaking search/suggestions.
- Keep stable public IDs, immutable sequence identity, Assay associations/version
  rules, lifecycle, experimental evidence, provenance and audit semantics.
- Preserve every existing server action signature, field name and submission
  behavior. A necessary contract change becomes a separate functional change.
- Keep CSV session, filter, formula safety, row count and audit contract. Keep
  upload disabling and existing attachment retention; never re-enable uploads
  through a new shared button or form.
- Per PR: format/lint/typecheck/unit checks, production build, applicable
  PostgreSQL and Chromium regressions, desktop/mobile screenshots, keyboard,
  focus, reduced motion, loading/error/empty/disabled states and sampled contrast.
  Add screen-reader and real-device checks before calling accessibility qualified.
- No merge until CI/protections and review are satisfied. Revert independently
  if a visual change alters behavior; do not repair business rules in a style PR.

## Pilot work still outstanding

R1-08: execute backup/restore on the future available host. R1-09: qualify HTTPS,
secure sessions and institutional identity where applicable. R1-10: data owner
curates the pilot subset; no invented dataset or unapproved import. R1-11: human
scientific acceptance. These remain distinct from UI work. Mac mini deployment
is deferred; `docs/deployment/PILOT_HOSTING_PLAN.md` stays preparatory.

# UI-04 — Scientific tables and lists

2026-10-31. User validated UI-03, base main `1faf7ba`. Delivery is a PR for
visual/functional review, **without merge**. No UI-05/06 or hosting work.

## Scoped inventory and before/after matrix

| Views / seam | Current information and behavior | UI-04 change |
|---|---|---|
| Oligos / RegistryTable | ID, name, DNA, length, GC, Tm, status; GET q; CSV retains q; API total/limit/offset | Semantic labeled scroll region, density, copy ID/DNA, numeric alignment, existing endpoint pagination |
| Targets / RegistryTable | ID, name, type, gene ID, status; GET q | Same shared table; complete long values via accessible disclosure |
| Assays / RegistryTable | ID, name, amplicon, version, status; GET q | Same shared table, numeric alignment |
| Experiments / RegistryTable | ID, assay version, performed time, protocol, status; GET q | Same shared table; keep version/provenance and existing assay lookup |
| Validations / RegistryTable | ID, status, conclusion, context, time; GET q | Same shared table; preserve evidence text |
| Projects / bespoke table | ID, name/owner, team, visibility, resource counts, status; GET q; array API | Reuse RegistryTable; no fabricated pagination or sorting |
| Team list / workspace cards | Real memberships, descriptions, member counts; linked detail | Preserve cards and role logic; shared readable list metadata |
| Team/project members / member-list | Identity, email, role; conditional remove and membership actions | Preserve controls; add explicit confirmation to existing removal |
| Admin / admin-list | User forms, teams/projects, method activation, vocabularies; server admin guard | Preserve real forms/roles; readable responsive list surfaces, no global form redesign |
| Global search / SearchSection | Six real resource groups, GET q, links and metadata | Preserve result contracts; wrap long content; no invented global sort |

Existing tests: registry creation/detail, search, lifecycle, visibility, workspace/
admin roles and mutation, CSV, scientific jobs, UI-02 keyboard/menu and UI-03
surfaces. Table links navigate explicitly; rows are not selectable or destructive.
Statuses already include text. No row-wide navigation or new business actions.

## Implementation plan

1. Capture baseline actual routes against deterministic isolated fixtures before
   product edits: empty/one/15/high-volume oligos, targets, assays, experiments,
   projects and existing contextual actions; desktop1440, mobile390, tablet768.
2. Preserve RegistryTable count/columns/server children contracts, add optional
   label/query/page/error props. Keep data fetching server-side; tiny client
   islands for density, clipboard and native confirmation only. Native details
   exposes full long values without relying on hover/title. No dependency.
3. Reuse existing tokens for flat scientific rows/header, numeric alignment,
   monospace DNA, focus/hover and contained scrolling. Comfortable/compact must
   differ measurably. Do not convert dense scientific tables to cards.
4. Keep GET q and CSV query untouched. Add navigation using existing API
   limit/offset only. Server ordering and supported filters remain unchanged;
   configurable sort/business filters are future work, not client-only substitutes.
5. Distinguish denied/session/error from empty and filtered zero results. Do not
   expose raw API errors or inaccessible identifiers. Preserve unmodified shared
   optional API helper for unrelated pages; registry-scoped result handling only.
6. Validate real DOM actions, copy/failure, keyboard, both densities, five widths,
   missing metadata and long values, roles/visibility and existing CSV/lifecycle.
   Run format/lint/typecheck/build/unit, PostgreSQL and full Chromium regressions.
7. Update evidence/results here and project tracking/memory, atomic commits,
   push and PR; inspect CI and protection rules. Stop before merge for user review.

## Risks and validation controls

No backend/API/schema/security or data semantic changes. No mock data in app
code. Fixture-only data lives in a separate tmpfs test project. Existing make
test-e2e deletes volumes, so use equivalent Compose steps without --volumes;
do not touch existing development/pilot volumes or containers. Baseline and after
must use identical deterministic input records, IDs/counts and fixed evidence
dates where displayed. No scientific result may be manufactured.

Browser runtime tools and Serena MCP unavailable; existing Playwright Chromium
is the fallback. No screen-reader/real-device/full WCAG certification claimed.

## Evidence and final results

External capture location: `/private/tmp/oligospace-ui04/{before,after}/`.
Matched pairs: `oligos-empty`, `oligos-one`, `oligos-fifteen`, `oligos-many`,
`targets`, `assays`, `experiments`, `projects`, `admin-actions`, `oligos-390` and
`oligos-768`. Additional after-only `oligos-compact` and `oligos-actions` show
the newly introduced interactions; they are not claimed as identical-state pairs.
The empty oligo pair is a zero-result search in a populated database; the real
initial zero-resource dashboard remains separately covered by UI-03's test.
Baseline and after use 55 deterministic private Oligos and the same Target,
Assay and run (fixed performed_at), with identical IDs/names/sequences/counts.
Only new confirmation/wide-text checks run subsequently outside these pairs.

Implementation uses `ScientificTableFrame`, `ScientificValue`, `CopyValue`,
`RegistryLoading` and `ConfirmRemoveButton`, composing existing server children
and actions. `registry-data.ts` handles list load failures locally, leaving the
general `apiGetOptional` behavior of unrelated pages untouched. `registry-page.ts`
normalizes unsafe offsets and encodes pagination URLs; an out-of-range page
offers a first-page link rather than claiming that the visible registry is empty.
No client-side sorting/filtering of a partial page is performed.

Initial baseline: 20 Chromium passed, four existing reference-stage skips.
PostgreSQL: 198 passed with migration round-trip. Format/lint/typecheck and
52 API/14 worker/4 web unit tests pass. Final production build and all 25 Chromium
tests pass, no skips. Exact-head CI results are recorded in the delivery PR.
Clipboard failure is tested by denying the
browser clipboard capability only, never by replacing application records/API.
The Playwright-only secure-origin argument allows clipboard on the existing
HTTP test origin; no deployment/network/security policy is changed.

Visual QA corrected prematurely truncated public IDs, short wide text without
disclosure, and test focus/scroll positioning in captures. Scoped independent
review identified the wide-text case; short values now wrap, while long values
have native keyboard-operable disclosure. A test navigation race was corrected
by waiting for logout to reach /login before selecting the next identity.
Loading boundaries also required waiting for the streamed table to become visible
before measuring rows or capturing evidence; hidden DOM row counts alone were
insufficient. The corrected test waits on rendered state, with no arbitrary sleep.

## Remaining differences and limitations

Production retains all original columns, real provenance and scientific units;
it does not copy the prototype's fictitious species/status filters or sample
counts. Rows remain explicit links plus copy controls, not new row-selection or
context-menu operations. Existing destructive membership forms gain a native
confirmation, with cancel/accept/reload persistence tested. No new destructive
table action exists. Missing values remain em dashes rather than inferred data.

High volume here means 55 matching entries crossing the existing 50-row API
boundary, not a benchmark of thousands of records. Lists with array endpoints
(projects/admin/team) retain their existing unpaginated API contract. Configurable
sorting, additional filters, saved views, virtualization and broader scale tests
are future functional work, not silently added in this style PR. Long tables use
an explicitly labeled, keyboard-focusable horizontal scroll region on smaller
screens. Density is local to the mounted table; no persisted user preference
is invented. Existing server status labels remain textual, not color-only.

UI-05 form interiors and UI-06 scientific workflow redesign are not started.
Rollback can revert this branch without any data/schema migration. User images
in `assests/` remain untouched/untracked. Do not merge before the user validates
this report and its before/after captures, even with green CI.

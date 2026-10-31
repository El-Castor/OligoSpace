# Scientific Soft UI — production tokens and primitives

2026-10-31. First implementation lot authorized by the user after preparation
PR #9. Base `d563165`; reference prototype `1aeec1a`, iteration 02. This implements
the existing migration plan, not another demonstration or a new roadmap.

## Scope and rollback

`apps/web/app/design-tokens.css` is the single production source for the adopted
palette, typography, spacing scale, elevation, radii, interactive borders and
semantic states. `globals.css` imports and consumes those tokens through existing
class contracts. Existing CSS variable names are retained; no React prop, input
name, server action, route, API, authorization, scientific value or database schema
changes. No dependency is added. Revert this lot's token/style changes to restore
the preceding appearance; no data rollback is involved.

Adopted: cool blue-gray canvas/surfaces, petroleum controls, native system/mono
type, stronger heading hierarchy, paired panel/button shadows, flat readable
fields/tables, neutral textual badges, warning/success/error surfaces, opaque
focus and disabled states, reduced-motion preference. Native validation and
server errors retain their existing transport and behavior. Danger styling only
uses existing explicit alert/invalid semantics, not inferred scientific status.

The prototype prefix is not duplicated into production. Shared selectors are
edited in place rather than adding a second override stylesheet. Historical
shell/page-specific styles are deliberately retained for their separate lots.

## Real application evidence

Captures use production Next routes backed by the API/PostgreSQL in the isolated
`oligospace-e2e` stack, not prototype routes or mocked responses. Runtime is the
existing production build, reached at `http://caddy:8080` inside that stack.
Only normal test fixtures exist in that disposable database; no fictional data
was added to production code or any development/pilot database.

Baseline and revised screenshots are external handoff artifacts under
`/private/tmp/oligospace-production-ui/{before,after}/`: dashboard-desktop,
registry-desktop, form-desktop and form-mobile (PNG). The revised set also covers
a real server validation error and a native disabled/focus style probe. The
disabled probe changes only the test browser's DOM attribute; it is visual
primitive evidence, not a claimed scientific workflow transition.

Desktop capture: 1440×1000; mobile: 390×844. Form overflow assertions also run at
320 and 768 px. Screenshot data timestamps/test names vary between fresh stacks;
compare presentation, not dynamic fixture text. Images were inspected against
the approved reference and baseline. No external browser dependency was installed:
the integrated browser tool was absent, so existing Playwright Chromium was used.

Functional evidence is separate from images: the existing Chromium journeys
cover login/logout, permissions and private-resource absence, scientific jobs,
Assay associations, lifecycle, evidence, disabled pilot uploads and authenticated
CSV download. New checks exercise real form navigation/server errors, focus,
sampled text/control/error contrast, reduced motion and responsive overflow.
All 198 PostgreSQL cases retain authorization/persistence coverage. Unit suites
and quality/build gates remain required. The delivery PR records exact results.

Final local result: format/lint/typecheck and production runtime builds pass;
52 API / 14 worker / 2 web unit tests, 198 PostgreSQL cases with migration
round-trip, and all 18 Chromium tests pass without skips. The new error test
targets the application's `.notice[role="alert"]`, avoiding Next's separate
navigation announcer. Scoped independent review found no important defect.

## Deliberate differences and next review

The legacy rail, brand, navigation geometry, topbar and mobile navigation behavior
are not yet migrated. Form composition remains the real multi-field workflow,
not the prototype's abbreviated mock form. Registry density/copy controls are
not added in this lot. Badges retain explicit text and neutral styling rather
than guessing a semantic color from scientific status. Dark theme remains pending.

These are staged boundaries, not claims of complete prototype fidelity. Some
legacy hard-coded shell/page colors remain outside the adopted primitive layer.
Contrast checks are sampled, Chromium-only; screen-reader/real-device and broader
contrast qualification remain open. The existing hidden mobile sidebar belongs
to the next shell/navigation lot, not a newly introduced behavior.

Next candidate after this visual/functional report: AppShell, navigation,
PageHeader and UserMenu presentation only, preserving `/me`, identity/session,
logout and server permissions. Do not start it until the user reviews this lot.

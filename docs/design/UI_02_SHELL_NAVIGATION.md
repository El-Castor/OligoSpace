# UI-02 — Scientific Soft UI production shell

2026-10-31. Authorized shell/navigation lot after PR #10, base `185c778`.
Reference: prototype `1aeec1a`, iteration 02, and the existing integration plan.
No registry-density, detailed form or scientific-page redesign is included.

## Visible changes and reference comparison

- 220 px sidebar, petroleum gradient `#456D76` → `#345761`, prototype outline DNA
  brand and consistent outline icons. Navigation retains all existing route groups,
  planned labels and conditional Admin link. Active section uses explicit
  `aria-current`, restrained inset elevation, border and font weight.
- Aligned 84 px desktop header, existing global search and real identity menu.
  Secondary navigation links back to the current route family; record/new labels
  are derived only from the URL, not fabricated workspace/project names.
- PageHeader retains its props and content, with semantic header markup, modern
  alignment and token spacing. UserMenu retains initials, identity/team links and
  the exact logout calls; Escape and focus leaving the menu close it accessibly.
- Below 768 px, a visible menu button opens a native modal dialog. Background is
  inert, navigation scrolls independently, Tab wraps at its endpoints, Escape
  closes and restores focus. Route changes and switching to desktop close it.
  A skip link targets the real main content. No mobile navigation is discarded.

The palette, 220 px rail, DNA icon language and inset active states match the
prototype. Production retains its richer information architecture and actual
scientific records, identity and notifications; it does not copy the mock profile
or dashboard counts. The mobile drawer is a native modal rather than the demo's
inline expanded menu, to keep background content inert. Secondary rail text is
slightly lighter than the initial candidate to meet sampled AA text contrast.
Table density, copy controls and later page compositions remain separate lots.

## Functional boundary and rollback

AppShell is still a server component fetching `/me`. It passes only the existing
server-derived Admin boolean into ShellNavigation. ShellLocation reads pathname;
it performs no API request. All original hrefs and the user-menu team selection
remain. Active project/team pages select their existing navigation family; no
new active-workspace state or selector is invented. Children render unchanged,
including loading/error/access-denied and unavailable-upload notices.

No backend, API, schema, policy, server action or scientific value changes. No
dependency added. Icons are code-native paths adapted from the approved specimen.
Revert the UI-02 component/token/style changes together for rollback; no data
rollback. Unrelated user images in `assests/` remain untracked and untouched.

## Evidence and qualification

Before/after actual Next production routes, backed by API/PostgreSQL on the
isolated `oligospace-e2e` stack, are saved externally under
`/private/tmp/oligospace-ui02/{before,after}/`. `shell-320`, `shell-390`, `shell-768`,
`shell-1024`, `shell-1440` compare the real dashboard shell; revised mobile-open
captures show the modal. Existing form/registry/error captures are retained too.
Screenshots contain disposable test-database fixtures, not new pilot data or
mocked responses. Browser/IAB is unavailable; existing Playwright Chromium used.

New E2E coverage exercises all five widths, no document horizontal overflow,
active routes, keyboard activation/Tab/Escape, focus return, resize with drawer
open, three roles' conditional Admin link, user-menu Escape/focus-out and logout.
Gradient endpoint contrast is measured for both normal and secondary rail text.
Existing E2E coverage separately verifies sessions, private-resource absence,
project membership, lifecycle, Primer3 persistence, upload policy and CSV.
PostgreSQL integration and unit/quality suites remain the functional evidence;
screenshots are not treated as proof of business correctness.

Validation found and corrected a non-deterministic native reverse-Tab boundary
with an explicit cycle and secondary text contrast of 4.40:1 on the light rail
endpoint by changing its token. Final local validation: 22 Chromium tests,
198 PostgreSQL cases with migration round-trip, and 52 API / 14 worker / 2 web
unit tests pass. Format/lint/typecheck and production builds pass. Exact CI
evidence is in the delivery PR.
Scoped independent review found no important issue. Limits: Chromium only,
sampled contrast, no real-device or screen-reader certification and no new
institutional OIDC qualification. Existing authentication contracts are preserved.

Stop after UI-02 integration and report; do not begin the next graphical lot
before the user's validation.

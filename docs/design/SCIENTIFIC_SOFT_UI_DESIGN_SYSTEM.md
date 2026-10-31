# OligoSpace — Scientific Soft UI

Prototype, 2026-10-31. Palette and structure approved by the user as the future
identity; production migration needs separate authorization. Dedicated
branch: `codex/scientific-soft-ui-prototype`. All displayed data and scientific
states are fictional; no Primer3 calculation, authentication or database is used.

## Direction and implementation boundary

Cool blue-gray surfaces, petroleum actions, cyan highlights and sage supporting
accents. Moderate neumorphism: exterior paired shadows on panels, a subtle inset
selected state, flat bordered tables/fields. Meaning never depends on shadow or
color alone. No violet, pink, glass effects or decorative scientific claims.

The existing app uses Next.js 16, React 19, TypeScript, CSS and native controls.
There is no installed component/icon library. The prototype reuses these
dependencies and component anatomy, but does not import production forms, shell
or API utilities: those carry authentication/server actions. Its separate Next.js
root is `apps/web/prototype`, launched with the web app's existing dependencies.
No production page, shared component, proxy/auth rule or API contract is changed.

## Tokens

Tokens live exclusively in `apps/web/prototype/app/tokens.css`, scoped to the
prototype root. Components consume semantic variables, never production globals.

| Family | Light reference | Use |
|---|---|---|
| Canvas | `#E9EEF0` | Cool blue-gray page |
| Surface / field | `#F1F5F6` / `#FAFCFC` | Raised panels / flat readable fields |
| Text / secondary | `#253A43` / `#52666F` | Primary and secondary readable copy |
| Primary | `#176B79` | White-text actions and selected navigation |
| Cyan | `#20A6B5` | Decorative accent; dark variant for text |
| Sage | `#5A9884` | Decorative accent; dark variant for text |
| Success / warning / danger | Dark green / ochre / brick | Labeled semantic states, no pink |
| Boundary | `#778B94` | Interactive edge; do not substitute shadow |
| Focus | Dark petroleum outline with surface gap | Keyboard focus, independent of elevation |
| Elevation | Soft dark lower-right + white upper-left | Panels; no nested raised-card stacks |
| Radius | 8 / 12 / 18 px | Control / panel / major surface |
| Space | 4 / 8 / 12 / 16 / 24 / 32 / 48 px | Consistent rhythm |
| Type | Native system sans; native monospace for sequences | No external font request |
| Density | Comfortable / compact | Row/field rhythm changes; labels stay legible |
| Motion | 120–160 ms for color/shadow | Disabled under reduced-motion preference |

Typography: 32–40 px main heading, 18–20 px panel headings, 14–16 px body/control,
12–13 px supporting copy. Tabular numbers; monospace sequences always marked 5′→3′.
Small line icons use one outline stroke language, decorative icons aria-hidden.

## Reusable component families

- Prototype shell: persistent desktop sidebar, mobile expandable navigation, skip link.
- Panel and metric: shared surface token; content hierarchy rather than icon decoration.
- Buttons: primary, secondary, quiet, disabled and selected/pressed states.
- Field: persistent label, native input/select/textarea, contextual help and error.
- Registry table: caption, scoped headers, sequences, textual status badges, horizontal
  scrolling confined to the table on small screens.
- Search/filter toolbar: local query and status filter, explicit reset, result count.
- Scientific-job row: fictional state, textual progress and explicit simulation notice.
- State panel: normal/loading/error/empty examples with live status or alert as needed.

The form only simulates local insertion. The new fictional row is lost on reload;
its status message says so. Buttons must not suggest a real write, export, validation
or calculation. Navigation points only within this demo.

## Accessibility and responsive rules

Target WCAG AA applicable criteria: text 4.5:1 (large text 3:1), interactive
boundaries/focus 3:1, keyboard operation, associated labels and persistent errors.
Cyan/sage base colors are not used as small text on the canvas. Disabled controls
remain labeled and their reason is stated; status badges include text and symbols.
Native browser validation supplements explicit form feedback; no copied domain
validation contract is introduced.

Desktop uses a 220 px navigation rail and a table/form split. Below 1100 px the
form moves below the registry; below 700 px the rail becomes a menu, metrics wrap
and controls stack. Dense tables keep semantic table markup and a labeled scroll
region; the document itself must not overflow horizontally. Test at desktop and
390 px mobile, keyboard and reduced motion. Automated contrast checks are evidence
for tested token pairs, not a claim of comprehensive WCAG certification.

## Dark-theme architecture (specification only)

Keep semantic variables separate from palette values. A future
`[data-theme="dark"]` overrides canvas/surface/text/border/elevation/status tokens,
without component-specific inverted colors. Proposed canvas `#17272E`, surface
`#20343D`, text `#E8F0F2`, primary `#8DD2DA`. Replace white highlight shadows with
restrained edge highlights; independently qualify contrast and focus. No partially
implemented or untested dark-theme toggle is shown in this first prototype.

## Validation record

Iteration 02 reinforces panel elevation (paired 7 px offsets, 16 px blur) and
button relief (4 px offsets, 8 px blur). Tables and fields retain flat borders.
The sidebar graduates from `#456D76` to `#345761`, with `#EAF3F4` text; tests
evaluate both gradient endpoints. Sequences have individually labeled copy
buttons and live success/fallback messages.

Compact mode reduces padding, species text, badges and copy controls while
preserving all columns. Chromium asserts row height below 85% of comfortable
mode. Synthetic plant examples feature *Brachypodium distachyon* Bd21/Bd21-3 and
*Arabidopsis thaliana* controls. No gene mapping or validation is asserted.

Actual commands, browser observations and screenshots are recorded in
`UI_COMPONENT_MIGRATION.md` after execution. This specification is a proposal;
production migration requires the user's visual approval.

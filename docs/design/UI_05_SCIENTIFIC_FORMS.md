# UI-05 — Scientific forms and editors

2026-11-01. UI-04 PR13 merged after user visual/technical approval, unchanged
head c0bb4ff and12 successful checks; merge985d506. Branch UI-05 starts from
synchronized main. User approval required before merging UI-05. UI-06 deferred.

## Inventory and design plan

| Forms | Existing fields / constraints / save / roles | UI-05 seam |
|---|---|---|
| Oligo create/edit | Name240, type, required DNA on create/immutable on edit, description/notes, workspace, lifecycle; existing POST/PATCH actions | Identity/sequence, annotation, access sections; read-only help, submit/error feedback |
| Target create/edit | Name240, type/organism, gene/transcript160, governed reference DNA, description, workspace/status; POST/PATCH | Biological identity, reference/annotation, access sections |
| Assay create/edit | Name/method, target, workspace, bp min1, °C step0.1, product/protocol, ordered oligo/role/label arrays, version/status; POST/PATCH | Identity, numeric design, associations, access; preserve repeated field ordering |
| Experiment create + inline update | Required assay/time, scope, protocol/version, JSON conditions/inputs, notes; existing actions | Context, protocol/evidence, access; JSON remains text, no unit conversion |
| Validation create | Assay/run, explicit supersession hidden field, result/time/conclusion required, JSON measurements/guidance/notes | Context, conclusion, measurements; preserve hidden server context |
| Project create/edit | Name200, team, visibility/status, description; existing actions | Identity/description and access; manager rules unchanged |
| Profile/team/admin | Existing role-guarded settings, membership, user/catalogue forms and saves | Shared field/action typography/pending button where applicable; no auth/catalogue redesign |
| Primer3 | Current parameter form, numeric units, server role checks, submit/retry, persisted jobs | Preserve form/workflow unchanged; only shared field/action presentation. Result/polling redesign UI-06 |

Current wrappers/labels/native controls already preserve names, units and schemas.
Problems: flat long grids, small secondary help, no shared submission feedback,
global unstructured server error, redirects lose entered fields. Existing tests
cover lifecycle/create/edit, roles, memberships, evidence/JSON, Primer3 and CSV.

Implementation: shared FormSection fieldsets/legends, existing field classes,
small client ScientificFormFrame/SubmitButton islands using native server actions
and useFormStatus. Keep form data server-rendered, action signatures/bindings,
names/types/min/max/step/readOnly/required and server feedback untouched.
Do not invent structured field errors from message text; native validity stays
field-associated, unstructured server failures remain a focused summary.
Use in-memory draft restoration for same-route error redirects only,
excluding hidden/action metadata, files/passwords, disabled/read-only controls.
The existing redirect remounts the page (observed in a targeted browser trace),
so a small FormDraftProvider in the unchanged AppShell main slot keeps one pending
submission across that remount, keyed by route and identity. Consume once on
error; clear on route/identity change, successful navigation/cancel/full reload.
No browser storage, draft API or silent sequence/number normalization. Restoring
selects must not reintroduce options removed by the server. Full reload/cancel/
successful navigation drops draft; never restore immutable sequence identity.
Supersession forms opt out of draft restoration: their hidden server-owned context
must not be reconstructed after the existing context-losing error redirect.
The error view directs the user back to the original evidence record. This
existing action limitation is preserved rather than silently changing provenance.

Known global viewer role can suppress scientific create/edit submissions using
existing /me; resource-specific edit policy remains authoritative server-side
(no complete frontend capability contract exists). Existing workspace manager
checks and denied mutation coverage must remain. No backend/policy changes.

## Validation and evidence plan

Before product edits capture actual production routes with fixed fixtures:
oligo new/edit/read-only/error/long values, target, numeric assay, experiment,
validation, project;1440 desktop and320/390/768/1024/1440 checks. Baseline and
after use identical input records/IDs/sequences/dates; no API/state mocks.
Use fresh separate tmpfs Compose project; no Docker volume deletion or deployment
changes. Evidence external `/private/tmp/oligospace-ui05/{before,after}`.
Test real save/reload, cancel, native validity, server failure and repeated
association values, keyboard/focus/help/read-only, role denial, pending/double
submission with delayed *real* request, exact units and Primer3/CSV regressions.
Run format/lint/typecheck/build, unit,198 PostgreSQL and full Chromium suite.
Review scoped diff, commit/push/PR/CI; stop before merge.

Serena and integrated browser runtime unavailable; existing Chromium fallback.
No new dependency, backend/schema/API or security-policy changes; no real data
or user image changes. No WCAG/screen-reader/real-device certification claimed.

## Results and limitations

Final local validation: format/lint/typecheck and production builds pass;
70 units(52 API/14 worker/4 web),198 PostgreSQL cases with migration round-trip,
28 Chromium tests passed without skips. Existing UI-02/03/04, auth, role,
cross-project visibility, lifecycle, CSV, upload policy and Primer3 jobs stay green.
New checks prove real pending request/one POST, readonly viewer routes, native
required validation, exact long text restoration, deliberate loss on full reload,
cancel, two repeated Assay failures and correct numeric/association persistence
after edit-route reload. Waiting for the completed edit navigation before reloading
fixed a new-test race; the persisted backend values were already correct.

The initial local-ref restoration was rejected by its failing E2E and replaced
with the scoped provider after proving page unmount/remount. React lint also
required moving ref mutation out of props into an owning callback; no lint rule
was disabled. Temporary diagnostics were removed. Scoped independent review of
both the forms and final retention/access boundaries found no important issue.

Official before/after pairs below use separate fresh test databases and the same
single scenario, not the full suite's accumulated fixtures. Baseline is an exact
git archive of main985d506 with the capture test added. After uses the actual
production image. Both create OLG-000001 with identical sequence/name, edit values
and empty other registries;1440×1000 desktop and390/768×1000 responsive captures.
The baseline error redirect loses fields; original values are explicitly re-entered
for its error screenshot, whereas after asserts automatic restoration. No other
application data or API response is mocked. The pending test delays a real POST,
then releases it and verifies persistence, rather than inventing a save response.

| Scenario | Before | After |
|---|---|---|
| Oligo initial | `/private/tmp/oligospace-ui05/before/oligo-new.png` | `/private/tmp/oligospace-ui05/after/oligo-new.png` |
| Error and long values | `before/oligo-error-long.png` | `after/oligo-error-long.png` |
| Edit / immutable sequence | `before/oligo-edit-readonly.png` | `after/oligo-edit-readonly.png` |
| Target | `before/target.png` | `after/target.png` |
| Assay with bp/°C | `before/assay-numeric.png` | `after/assay-numeric.png` |
| Experiment | `before/experiment.png` | `after/experiment.png` |
| Validation | `before/validation.png` | `after/validation.png` |
| Project | `before/project.png` | `after/project.png` |
| Mobile390 / tablet768 | `before/assay-390.png`, `before/assay-768.png` | `after/assay-390.png`, `after/assay-768.png` |

All abbreviated paths are under `/private/tmp/oligospace-ui05/`. Full-suite
captures/diagnostics are separate under `functional/` and `playwright-results/`.
Screenshots were inspected against the baseline and approved specimen. Production
keeps all its scientific fields, workspace controls, JSON evidence, units and
provenance; the prototype's simulated local form is not ported. Real long forms
therefore use multiple scientific sections rather than the demo's small side panel.

Components: FormSection, ScientificForm/ScientificFormFrame, SubmitButton and
FormDraftProvider. Existing six resource form props/action signatures unchanged;
supporting profile/admin/team/project-member/inline-maintenance and Primer3 submit
buttons share pending presentation without changing their server guards/actions.
AppShell DOM/navigation/auth remain intact; only its children receive an invisible
client context keyed by the existing server identity. UI-04 tables unchanged.

Limits: no persisted/autosaved drafts or restoration after full reload; no hidden
supersession context reconstruction. Unstructured server errors stay a focused
summary, native field errors retain browser validation; no heuristic field-error
mapping or schema change. Resource-specific edit capability is still enforced by
the server, not reimplemented in frontend policy; existing denied-edit E2E remains.
Known viewer role suppresses scientific form submission, but profile remains
editable as before. Array selectors keep server-visible options and original order.
No global form/workflow redesign, dependency or production dataset added.

UI-06 result/job/polling/evidence redesign not started. UI-05 PR must stay OPEN
until user's explicit capture/report approval, even after green CI. Revert this
frontend-only lot for rollback; no data/schema rollback. User images remain
untouched/untracked. Test stacks are stopped without Docker volume deletion.

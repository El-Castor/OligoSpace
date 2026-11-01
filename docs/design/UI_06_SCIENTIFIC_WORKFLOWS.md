# UI-06 — Scientific workflows and interaction polish

2026-11-01. UI-05 PR14 merged at eb7f2b2 after explicit user approval, unchanged
head fb6b661,12 green checks/no conflict. UI-06 starts from synchronized main.
UI-06 delivery stops at an open PR pending explicit visual/functional approval.

**Integration update — 2026-11-01:** the user subsequently approved the visual
and functional report and explicitly authorized PR #15. Exact head
`535454ef6a12de0815dec8ef21546695625fb9a8` retained,12 checks
`COMPLETED/SUCCESS`, `CLEAN/MERGEABLE`; merged by merge commit
`9852bdd704dc2658dd2941eeae8adb56f8ddc759`. main synchronized by fast-forward.
This approval supersedes the review hold recorded below; no subsequent functional
lot is authorized. Next work is documentation-only MVP qualification preparation.

## Scoped inventory and design

| Existing surface | Actual contract | UI-06 presentation |
|---|---|---|
| Primer3JobSection on Oligo/Assay | QC and stored Forward/Reverse compatibility only; existing role-controlled action | Parameter grouping, units, restrained surfaces; unchanged names/min/max/step/defaults and action |
| FactCard/Result | Stored Tm/hairpin/dimers/delta/end complementarity; two-decimal display and existing unit mapping | Readable value/method hierarchy, no new computed fact or rounding |
| Job history | API order, IDs/state/errors, version mismatch, raw provenance | Textual state badge, real timestamps, input sequence snapshot, copy controls, attempt history and raw values |
| ScientificJobAutoRefresh | GET router.refresh every1500ms while queued/running/retrying, max40 refreshes, cleanup | Expose honest refresh feedback/limit and manual GET refresh, no percentage |
| /scientific-jobs/[publicId] | Authorized persisted history; no existing frontend retry form | Same historical facts, source navigation, explicit load failure distinct from not-found |
| Existing submit actions | Same API payload, parameters and idempotency key behavior | Reuse UI-05 pending submit; no retry/cancel API invented |

Backend states are exactly queued/running/retrying/succeeded/failed. No cancelled,
expired, percentage-complete, BLAST/mapping or primer-design selection workflow is
implemented here. This is existing QC/pair compatibility, not experimental proof.
Worker/scheduler/recovery/idempotency/schema/API remain untouched. Error and stale
version warnings must remain visible, even alongside results. Preserve all raw
metadata and original numerical formatting; sequences come from persisted input,
never from the current edited source or a mock.

## Implementation and validation plan

1. Seed real successful QC/pair jobs, a real worker timeout failure and a queued
   request in a separate tmpfs test stack. Worker control affects that project only;
   fault injection is explicit and never writes fabricated scientific results.
2. Capture exact main eb7f2b2 before product edits, then render after against the
   *same persisted job rows* for identical IDs/parameters/timestamps/values.
   Capture parameters, queued/success/failure, history, pair/stale version,
   longest supported60nt QC input, desktop1440/mobile390/tablet768.
3. Shared state/input helpers, unchanged FactCard precision, explicit input/result
   copy and bounded raw/attempt panels. Reuse UI02–05 controls/tokens.
4. Add unit cases for actual/unknown states and missing/snapshot input shapes;
   add a normal real-worker E2E for copy/history/keyboard/five widths. Keep full
   role/visibility/lifecycle/CSV/Primer3 regressions. Separate controlled evidence
   runner from the default suite; no skipped new standard tests.
5. Run format/lint/typecheck/unit/build, PostgreSQL and full Chromium; inspect
   before/after against approved prototype, review diff, commit/push/PR/CI.
   No merge before user's approval; no hosting/Cloudflare or volume deletion.

Serena and integrated browser runtime unavailable; existing Playwright fallback.
No new dependency. Temporary test-only Compose overrides/controls stay external.

## Evidence and results

External evidence `/private/tmp/oligospace-ui06/{before,after}`. Running
and retrying may be too transient for reproducible paired captures; report actual
coverage and do not freeze invented database states. No real-device/reader/WCAG
certification. Historical provenance, recovered-job behavior and genuine errors
take precedence over a cosmetic resemblance to simulated prototype progress.

### Implemented components and invariants

ScientificJobCard composes actual job state, persisted timestamps, input sequences,
attempt details and raw result/provenance. Primer3Result is extracted unchanged:
same fact ordering, `Number(value).toFixed(2)`, method/mode and degC→°C display.
No GC/length or biological conclusion is recomputed in this job view; existing
source-record metrics remain available through source navigation. CopyValue copies
exact stored ID/DNA or JSON.stringify(payload,null,2), not rounded card values.
The parameter form keeps every original field/default/min/max/step and server
action. No retry/cancel button or new scientific operation is introduced.
The backend does have POST /scientific-jobs/{id}/retry, guarded by submit role,
requester/admin, retryable error and remaining attempts. It had no frontend form;
this lot preserves that UI behavior. The observed timeout failure exhausts all3
attempts and cannot be manually retried under the existing rules. Automatic
retry remains visible in genuine attempt history; no eligible state is fabricated
to demonstrate a new button. Job visibility continues to require the source and,
for a pair, both input Oligos to be visible under the existing repository query.

ScientificJobAutoRefresh still polls every1500ms at most40 times while the active
boolean stays true, with cleanup and manual GET refresh. Its limit is now visible
as a pause/last-observed-state notice. Independent review found that an initial
active-job-ID React key reset the budget when another job completed; removing
that key preserves the original lifecycle. A pure timer-controller test exercises
39 ticks, a still-active job set after another completes, the40th tick/stop and
cleanup. No timer reset on changing active identities.

Job detail keeps private/forbidden jobs not-found and shows generic service/session
failure without guessing state. A proposed streaming loading boundary was removed:
E2E proved that it flushed HTTP200 before private-job notFound; original HTTP404
is retained rather than weakening the permission regression test. New attempt
rows repeat state text legitimately; E2E selectors now target the global job
status role instead of matching all identical history-cell text.

### Real evidence, reproduction and coverage

The explicit `e2e/workflow-evidence.ts` runner is separate from default *.spec.ts.
It creates real jobs through actual app forms. Host control markers start only
`oligospace-ui06-test`'s worker, briefly recreate it with test-only
`SCIENTIFIC_TOOL_TIMEOUT_SECONDS=0.0000001`, then stop it. This produces two real
successes, a timeout failure after3 actual attempts, and a queued request. No SQL
state/result injection, mock response or invented scientific value. The first
manual controller ran too late for the90-second wait; automatic marker control
then completed the reference scenario successfully.

Manifest: OLG-000001 (60nt), ASY-000001, SJOB-000001 QC success, SJOB-000002 pair
success, SJOB-000003 timeout failure, SJOB-000004 queued. An actual protocol edit
makes the pair job historical v1 against current Assay v2. Backend job rows are
identical across before/after: ordered row-JSON MD5
`8502b8e5b29708c3e7eec8139de7da29` on both sides. QC displayed facts remain
77.87°C,72.07°C,67.79°C from real Primer3 output; these are test inputs, not
experimental recommendations. Only the web container/image changes between the
two capture runs; API/PostgreSQL remain running with the worker stopped.

| Same persisted scenario | Before | After |
|---|---|---|
| Parameters and3-job QC history | `before/parameters-history.png` | `after/parameters-history.png` |
| Queued request | `before/queued.png` | `after/queued.png` |
| Completed QC /60nt input | `before/result-long-sequence.png` | `after/result-long-sequence.png` |
| Failed /3 attempts | `before/failed.png` | `after/failed.png` |
| Stored Forward/Reverse pair | `before/pair-result.png` | `after/pair-result.png` |
| Historical Assay version | `before/stale-version.png` | `after/stale-version.png` |
| Mobile390 / tablet768 | `before/result-390.png`, `before/result-768.png` | `after/result-390.png`, `after/result-768.png` |

All paths are under `/private/tmp/oligospace-ui06/`; manifests, external test-only
Compose overrides, controller and evidence config document this local run.
Default full-suite captures/diagnostics are separate under functional/ and results/.
Reference and after evidence each pass on the same database, with a direct
assertion of unchanged fact-card values. Running/retrying windows were transient
and not frozen for paired screenshots. Timeout retries/attempt history are real;
an actual worker-kill/recovery qualification was not repeated in this graphical
lot. Existing recovery/lease/idempotency code and regression tests stay unchanged.

Final local gates: format/lint/typecheck and production build pass;74 units
(52 API/14 worker/8 web),198 PostgreSQL with migration round-trip,29 Chromium
tests all pass. New E2E verifies exact ID/60nt input/raw-result clipboard contents,
attempt disclosure via keyboard, provenance parameters/version, reload persistence,
no fake progressbar and no page overflow at320/390/768/1024/1440. Existing auth,
role/private-job404, cross-project visibility, lifecycle, CSV and Primer3 pair/
ambiguous-input journeys pass. Scoped independent review's polling finding fixed
and reviewed; no remaining important issue found. Chromium only; touch hardware,
screen readers and institutional OIDC remain unqualified. No new dependency or
backend/API/schema/worker/scheduler/deployment change. No real data/volume deletion.

### Series UI-02 through UI-06

- UI-02 (PR11): real AppShell, petroleum navigation, responsive modal and roles.
- UI-03 (PR12): common surfaces, natural panel heights and clearer metadata.
- UI-04 (PR13): scientific tables, density/copies and existing API pagination.
- UI-05 (PR14): grouped forms, pending/errors and bounded in-memory drafts.
- UI-06 (this unmerged PR): real scientific execution state/results/history and
  provenance polish. Prototype mock progress/results never enter production.

UI-02–05 are integrated; UI-06 awaits user's explicit approval before merge even
with green CI. The scientific backend and pilot qualification remain distinct:
no claim of experimental validation, full accessibility or operational hosting.
Rollback reverts frontend presentation only; no data/schema rollback. Official
prototype branch remains preserved and unmerged; personal assests/ images remain
untouched/untracked. Test stacks are stopped without deleting Docker volumes.

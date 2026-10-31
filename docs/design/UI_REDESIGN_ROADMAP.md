# Progressive UI migration — proposal after prototype review

2026-10-31. Requested visual migration estimate, not an activated execution plan.
This does not replace the functional roadmap. R1-06 and R1-07 remain prioritary;
no production UI migration or merge is authorized by creating this document.

Estimates are inferred developer-days for one implementer, include relevant QA,
exclude user review delay, and must be refined after prototype feedback.

| Batch | Scope | Depends on | Estimate |
|---|---|---|---:|
| UI-01 | Review prototype, settle tokens, accessibility/density and dark specification | User visual approval | 0.5–1 d |
| UI-02 | Add scoped semantic tokens and shared control/field/panel primitives; preserve old styles | UI-01; R1-06/R1-07 integrated | 1–2 d |
| UI-03 | Navigation, responsive shell, header and identity menu | UI-02 | 1.5–2.5 d |
| UI-04 | Oligo/Target/Assay lists, search, filters and confirmed CSV control | UI-02, UI-03, R1-07 | 2–3 d |
| UI-05 | Record details and scientific forms; preserve errors, names/actions and scope choices | UI-04 | 2–3 d |
| UI-06 | Primer3 history/provenance and experimental evidence; respect disabled-upload policy | UI-05, R1-06 | 1.5–2.5 d |
| UI-07 | Workspace/admin/auth surfaces and cross-page responsive/accessibility regression | UI-03–06 | 2–3 d |

**Light-theme total: 10.5–17 developer-days**, including review/QA, before adding
new functional modules. Dark-theme implementation and independent contrast/visual
qualification: an additional 2–4 days. These are planning estimates, not commitments.

Each batch: dedicated branch and small reviewable PR; unchanged API/auth/scientific
contracts; Next build, lint, typecheck, existing units and relevant Chromium tests;
desktop/mobile screenshots, keyboard/focus and contrast review. Integration needs
explicit user authorization. Screenshot approval is not approval to rewrite forms.

Stop only the affected visual batch if a component requires a functional contract
change; handle that through the existing functional workstream instead. Keep mock
data inside the isolated prototype and the main branch immediately available for
R1-06/R1-07. Do not add libraries or restructure routing without a demonstrated need.

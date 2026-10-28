# Primer3 2.6.1 qualification

Validated on 2026-09-07 in the production worker image built from
`infra/docker/bioinfo-worker.Dockerfile`.

## Qualified contract

- Source: Primer3 `v2.6.1`, archive SHA-256
  `805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e`.
- Effective runtime version: `libprimer3 release 2.6.1` from
  `primer3_core --about`; a mismatch is a terminal provenance error.
- Nearest-neighbor Tm: `oligotm`, `-tp 1` (SantaLucia 1998 thermodynamic
  parameters), `-sc 1` (SantaLucia 1998 salt correction).
- Hairpin: `ntthal -r -a HAIRPIN`.
- Homodimer and pair heterodimer: `ntthal -r -a ANY`.
- Pair 3′-end complementarity: `ntthal -r -a END1`.
- Concentration mappings: `-mv` and `-dv` in mM, `-n` dNTP in mM, `-d`
  oligo concentration in nM, and `-maxloop` in nucleotides.
- Accepted input: non-empty unambiguous DNA (`A/C/G/T`) no longer than the
  effective and server-bounded `max_nn_length` of 60 nt. Longer or ambiguous
  sequences are explicitly unavailable; no alternate Tm formula is substituted.

The Reverse Assay oligo is supplied to thermodynamic calculations exactly as its
stored 5′→3′ sequence. It is not reverse-complemented by the wrapper.

## Golden pair fixture

Parameters: 50 mM monovalent salt, 1.5 mM divalent salt, 0.6 mM dNTP,
50 nM oligo, maximum loop 30.

- Forward: `ATGCGTACGTTAGCGTACGA`
  - nearest-neighbor Tm: 59.626630 °C
  - hairpin: 69.836183 °C
  - homodimer: 46.168760 °C
- Reverse: `TCGTACGCTAACGTACGCAT`
  - nearest-neighbor Tm: 59.626630 °C
  - hairpin: 69.091431 °C
  - homodimer: 34.346077 °C
- absolute Tm delta: 0.000000 °C
- heterodimer (`ANY`): 59.555182 °C
- 3′ end complementarity (`END1`): 59.555182 °C

These are thermodynamic tool facts and do not constitute an experimental
compatibility, amplification-efficiency, validation, or specificity conclusion.

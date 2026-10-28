# Bioinformatics methods

## Initial calculations

Input is uppercased and ASCII whitespace is removed. Accepted DNA symbols are the
IUPAC DNA alphabet. Length and GC percentage count symbols directly; GC percentage
is only emitted for unambiguous A/C/G/T sequences. Reverse complement supports the
IUPAC complement table.

The first API calculation uses the Wallace rule (`2 × (A+T) + 4 × (G+C) °C`) only
for unambiguous short DNA and reports method and parameters. It is a reproducible
screening value, not a claim about assay conditions. It remains labeled “Wallace
screening Tm” and is never relabeled as a Primer3 nearest-neighbor result.

## Exact target mapping

The mapping service searches the normalized oligo and its reverse complement in the
provided target sequence, reports every zero-based half-open match, strand, total
match count, and ambiguity warning. Palindromic sequences are not double-counted.
Results must store algorithm version, parameters, target/reference version, and
timestamp. Genome-wide specificity is not inferred from target-only exact mapping.

## External tools

Primer3 records executable/library version, source checksum, requested and effective
parameters, immutable input sequence/digest, job and attempt identity, UTC execution
times, wrapper/worker/build identity, results, warnings, unavailable states, and safe
errors. BLAST adapters will record equivalent database/reference provenance and a
raw-result object key where result size justifies object storage. Reference FASTA/GFF data is never
invented and is not bundled unless licensing and provenance permit it.

The worker image pins BLAST+ 2.17.0 from NCBI's immutable release directory and
verifies NCBI's published checksum for each supported Linux architecture (ARM64 and
x86_64). Primer3 2.6.1 is compiled in a separate build stage from the official,
SHA-256-pinned source release. The runtime invokes `oligotm` and `ntthal` with explicit
monovalent, divalent, dNTP, and DNA concentrations; it records the SantaLucia 1998 Tm
and salt-correction methods. The worker accepts only unambiguous A/C/G/T for these
thermodynamic calculations and reports measured tool facts separately from human or
policy interpretation. BLAST is installed separately because the requested
conda-forge package is unavailable on Linux ARM64.

## Qualified Primer3 scientific jobs

Plan 005 exposes two persistent job kinds: individual Oligo QC and selected
Forward/Reverse Assay analysis. The accepted parameter schema is allow-listed and
bounded. `oligotm -tp 1 -sc 1` produces SantaLucia 1998 nearest-neighbor Tm;
`ntthal -r` retains `HAIRPIN`, `ANY`, and `END1` as distinct method modes for
hairpin, homodimer/heterodimer, and 3′-end complementarity respectively. Reverse
Assay oligos are passed exactly as stored 5′→3′ and are not reverse-complemented.

Only non-empty unambiguous A/C/G/T DNA of at most 60 nt is accepted for this
qualified contract. No Wallace or long-sequence fallback is substituted. Pair output
contains the two individual fact sets, absolute Tm delta, heterodimer and end facts,
but never a biological pass/fail, specificity, amplification, or validation claim.
Exact options, units, source checksum, limitations and measured fixtures are recorded
in `docs/PRIMER3_QUALIFICATION.md`.

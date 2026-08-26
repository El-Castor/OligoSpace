# Bioinformatics methods

## Initial calculations

Input is uppercased and ASCII whitespace is removed. Accepted DNA symbols are the
IUPAC DNA alphabet. Length and GC percentage count symbols directly; GC percentage
is only emitted for unambiguous A/C/G/T sequences. Reverse complement supports the
IUPAC complement table.

The first API calculation uses the Wallace rule (`2 × (A+T) + 4 × (G+C) °C`) only
for unambiguous short DNA and reports method and parameters. It is a reproducible
screening value, not a claim about assay conditions. Primer3 nearest-neighbor Tm,
hairpin/dimer analyses, and pair compatibility belong to the worker phase.

## Exact target mapping

The mapping service searches the normalized oligo and its reverse complement in the
provided target sequence, reports every zero-based half-open match, strand, total
match count, and ambiguity warning. Palindromic sequences are not double-counted.
Results must store algorithm version, parameters, target/reference version, and
timestamp. Genome-wide specificity is not inferred from target-only exact mapping.

## External tools

Primer3 and BLAST adapters will record executable/library version, database/reference
checksum, parameters, and raw-result object key. Reference FASTA/GFF data is never
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

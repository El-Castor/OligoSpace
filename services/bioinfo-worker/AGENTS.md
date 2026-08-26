# Bioinformatics worker scope

- Analyses are deterministic for identical inputs, versions, and parameters.
- Record algorithm/tool version, parameters, reference identifier/checksum, start
  and completion timestamps, and warnings with every result.
- Never infer experimental validation or specificity from incomplete evidence.
- Use small documented fixtures in tests; do not commit restricted genomes.
- Put wrappers behind service interfaces so Primer3/BLAST implementations can be
  upgraded without coupling callers to tool-specific output.
- Long-running work belongs in the queue, not HTTP request handling.

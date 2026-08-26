# Oligo database migration report

- Audit date: 2026-08-26
- Source: `Oligo_database_CP.xlsx` (read-only, outside repository)
- Current SHA-256: `35fdbf1931f55ddd566838639fdf8cadadcd790ba72cb2c3aac52f04b06e3f55`
- Mode: preview/audit only; no rows imported and no source cells modified

The source file changed externally during the audit. The first observed snapshot
had SHA-256 `3d1e3cf079ec5c9f6aec3fa540db90e4356e011b11049ee9e6f48d1bacb1b67b`
and was approximately 26.9 KB. The current snapshot is 31,536 bytes and has the
checksum above. OligoSpace did not open or save the workbook in write mode. Results
below refer to the current snapshot; confirmation must pin the reviewed checksum.

## Workbook structure

| Sheet | Non-empty XML rows | Interpretation |
|---|---:|---|
| Oligo-probes CP database | 460 | Header, 100 candidate records, 359 allocated ID-only placeholders |
| Experiments | 48 | Header, example/allocated experiment IDs; no populated experiment details |
| Lists | 17 | Status/application/direction/validation controlled-value draft |
| Sonde template | 2 | Header and T7 template sequence |

## Preview outcome

- Candidate oligo rows: 100.
- Importable after row-level validation: 93; accepted/imported: 0 because this is a
  preview and database confirmation was not requested.
- ID-only rows skipped from candidate import: 359 (`O0100` through `O0458`).
- Application values: PCR 38, qPCR 31, HIS 31.
- Direction values: Forward 49, Reverse 50, and `F` 1.
- Recorded validation values: Not tested 99 and Validated 1 in the current snapshot.

## Normalization proposed, not silently applied

- Trim ASCII surrounding whitespace from text fields while preserving original
  source values in import evidence.
- Normalize sequence whitespace/case only after validation.
- Map direction `F` to `Forward` with an explicit warning (`O000EX`).
- Map source applications to administrator-managed ExperimentTypes during confirmed
  import; do not hard-code them as an oligo property.
- Interpret Excel date serials through openpyxl in the production preview, retaining
  original values.

## Blocking data-quality findings

- Example/template record `O000EX` contains `ATGCGT...`; it is not a valid sequence
  and must be skipped unless explicitly corrected in a new source artifact.
- Six records contain non-sequence text `Pas spécifique a refaire.`: `O0036`,
  `O0037`, `O0054`, `O0055`, `O0084`, `O0085`.
- `O0008` declares length 42 while its sequence contains 43 nucleotides. Both the
  entered and calculated values must be retained in migration evidence.

## Possible duplicates and storage conflicts

No exact duplicate valid sequence was found among candidate rows by uppercase,
whitespace-free comparison. Reverse-complement duplicates will be included in the
production importer preview.

Two physical locations are assigned to multiple records and cannot be converted to
unique occupied stock positions without review:

- `Freezer-20 167 / Box 1 Oligo-Probes / A7`: `O0007`, `O0008`, `O0009`.
- `Freezer-20 167 / Box 1 Oligo-Probes / A9`: `O0011`, `O0012`, `O0013`.

These could represent reused text, colocated tubes, or incorrect positions. The
importer will report them and must not guess.

## Ambiguities and missing mandatory fields

- The spreadsheet mixes biological, assay, order, validation, and stock facts; the
  importer will decompose them rather than reproduce the sheet as one table.
- Direction is contextual and will become an `AssayOligo` role.
- Target cells combine aliases and gene IDs with inconsistent delimiters; no gene
  identity is inferred without a reviewed parsing/mapping rule.
- Candidate rows have names, but seven sequences are invalid (including the example
  row); those rows fail mandatory biological-identity validation.
- The earlier snapshot appeared to lack sequences and many validation values in
  later rows; because the file changed, those observations are retained as snapshot
  history and are not attributed to the current workbook.

## Next migration step

The openpyxl-based preview was regenerated in the pinned API environment on
2026-08-26 and matches this audit: 100 candidates, 93 importable records, seven
rejections, 359 allocated-only rows, and zero imports. Review target decomposition
and storage conflicts with a data owner, pin the reviewed source checksum, then
require explicit confirmation before any database writes.

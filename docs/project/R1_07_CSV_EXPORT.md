# R1-07 — Scientific oligo CSV, schema v1

2026-10-31. Implements confirmed D9. Scope: oligonucleotides only; no extended
Assay/Target/stock export and no invented organism or validation relationship.

## API and browser contract

Authenticated `GET /api/v1/registry/oligos/export.csv?q=...` reuses `list_visible`
and the same literal search (ID/name/normalized sequence) as the oligo list.
Every global role may export only currently visible records in its organization;
project/team membership and revocation apply identically. All matching records
are exported, not only the first displayed page. No status filter is invented;
active/deprecated/archived records follow the existing list behavior.

The authenticated Next route `/oligos/export?q=...` forwards the server session
through the existing API helper. The oligo list links to it using its current
query. No tokens enter the URL or browser CSV. Errors return JSON and no download.
Files use `oligos.csv`, UTF-8 with BOM, comma delimiter, CRLF record separators,
all fields quoted and internal quotes doubled. Embedded Unicode/newlines survive
CSV parsing. Null is empty, zero remains zero. Formula-risk text is prefixed with
an apostrophe (leading =/+/-/@ after whitespace, or initial tab/CR/LF); consumers
must treat that apostrophe as the documented spreadsheet safety transformation.

Maximum 1,000 rows and 8 MiB including BOM. Over either bound: 422
`export_too_large`, refine the search; no truncation or success audit. Generation
is bounded and in memory, not a bulk streaming/archive facility. Successful
responses are `no-store`, `nosniff`, with `X-Export-Schema: oligos-csv/v1` and
`X-Export-Row-Count` equal to actual emitted data rows. Empty results contain the
header and a zero count.

## Ordered columns

| Columns | Meaning |
|---|---|
| public_id, name | Stable public identifier and user-provided name |
| normalized_sequence, oligo_type, status | Stored 5′→3′ identity, declared type and lifecycle |
| sequence_length | Stored nucleotide length |
| gc_percent, melting_temperature_c, molecular_weight_g_mol | Stored screening metrics; absent values remain empty |
| normalization, gc_method, tm_method, molecular_weight_method | Stored algorithm/version provenance, never inferred |
| calculated_at | Stored calculation timestamp |
| created_at, updated_at | Stored record timestamps, ISO 8601 |

Tm is the existing Wallace screening estimate when `tm_method` says so; it is
not a Primer3 nearest-neighbor result. Ambiguous sequences preserve unavailable
metrics and methods. No user UUID/email, internal scope UUID, notes, credentials,
unrelated project metadata or synthetic biological result is exported.

## Audit and evidence

One `export` / `oligo_export` event is committed before a successful response:
actor, UTC timestamp, request correlation, schema, row count and a boolean
`search_applied`. The query itself, CSV body and sequences are not audit facts.
The event identifies the export operation, not a scientific record; it proves
generation, not that the browser received/read every byte. Failed/oversized
exports create no success event; scientific records remain unchanged.

Tests extend the existing R1-04 role/audience/scope matrix to CSV and membership
revocation. Separate PostgreSQL cases parse quoted Unicode/multiline/formula
names, compare stored sequence/provenance, check ambiguous metrics, persisted
audit and no-session refusal. Unit cases cover formula prefixes, null and zero.
Bound tests lower constants to exercise rejection without large fixtures; they
do not qualify bulk throughput. Chromium downloads as a viewer with the current
query, checks BOM/quoted Unicode and excludes another user's private record.

# Product specification

## Product promise

OligoSpace helps a research team find, assess, reuse, validate, and physically
locate oligonucleotides and reusable assays without confusing a sequence with a
tube or a methodological category with an experiment execution.

## Primary workflows

1. Search before creating; reuse an existing biological sequence when appropriate.
2. Register a target and oligo with computed sequence QC and source provenance.
3. Define an assay using contextual roles such as forward, reverse, and probe.
4. Map assay oligos to a reference sequence and inspect ambiguity visually.
5. Record an experiment run and contextual validation without overwriting history.
6. Order a synthesis lot, register stock, move/consume it through immutable events.
7. Export or audit records with stable IDs and visible provenance.

## MVP boundary

The first milestone supplies the development stack, OIDC boundary, relational core,
basic registry API, dashboards/navigation, read-only Excel preview framework, and
scientific unit tests. Experiment runs, validation UI, inventory workflows, object
uploads, full-text search, mapping visualization, worker execution, and production
backup automation are subsequent phases and must not be represented as complete.

## Product principles

- Search and reuse beat silent duplication.
- Contextual validation beats global booleans.
- Actionable summaries beat decorative dashboards.
- User-entered, calculated, inferred, and experimentally validated facts are
  visibly distinct.
- Important scientific records are deprecated or versioned, not silently erased.

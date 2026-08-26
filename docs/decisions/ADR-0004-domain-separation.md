# ADR-0004: Separate biology, assay context, and inventory

- Status: accepted
- Date: 2026-08-25

## Context

The source spreadsheet mixes sequence identity, primer direction, validation,
orders, and tube location. Those facts have different lifecycles and meanings.

## Decision

Model biological `Oligo`, contextual `AssayOligo` role, reusable `Assay`, executed
`ExperimentRun`, contextual `Validation`, synthesized `OligoLot`, physical
`StockItem`, hierarchical `Location`, and immutable `InventoryEvent` separately.

## Alternatives

A giant oligo table is easy to import but produces contradictory data and loses
history. Treating every tube as an oligo duplicates biological identity.

## Consequences

Imports require explicit decomposition and warnings. Queries use more joins, while
reuse, provenance, validation, and stock history become scientifically coherent.

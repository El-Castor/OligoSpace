# API scope

- Routes validate transport concerns and delegate to services; keep scientific and
  authorization policy outside route handlers.
- Keep domain concepts distinct: `Oligo` is biological identity, `AssayOligo` is
  contextual role, and lot/stock models are physical inventory.
- Use typed SQLAlchemy 2 models, Pydantic schemas, repositories for persistence,
  and explicit transactions in services.
- Enforce authorization on every non-public endpoint. Add tests for role and
  visibility boundaries when changing access rules.
- Every schema change needs a reversible Alembic migration, indexes/constraints,
  and PostgreSQL-aware tests where behavior differs from SQLite.
- API errors use stable problem codes; never expose tokens, secrets, or internals.

# The Shatranj Heritage — API

FastAPI backend for The Shatranj Heritage, structured as a modular monolith (`app/modules/<domain>/`) per [docs/Software Requirements Specification.md](../../docs/Software%20Requirements%20Specification.md) and [docs/Implementation Plan.md](../../docs/Implementation%20Plan.md).

See the [repository README](../../README.md#local-development) for setup instructions (Docker Compose or running natively).

## Layout

```
app/
  core/       Settings, DB session, logging, standard response envelope
  modules/    One package per business domain (auth, catalog, inventory,
              cart, orders, payments, shipping, cms, admin, notifications).
              Each currently exposes a scaffold placeholder router; real
              endpoints land as each module's implementation phase begins.
  api/v1/     Aggregates all module routers under /api/v1
migrations/   Alembic, wired to app.core.database.Base.metadata
tests/
```

## Scripts

```bash
ruff check .            # lint
ruff format --check .   # format check
pytest -q               # tests
alembic upgrade head    # apply migrations
alembic revision --autogenerate -m "message"   # new migration
```

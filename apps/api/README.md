# The Shatranj Heritage — API

FastAPI backend for The Shatranj Heritage, structured as a modular monolith (`app/modules/<domain>/`) per [docs/Software Requirements Specification.md](../../docs/Software%20Requirements%20Specification.md) and [docs/Implementation Plan.md](../../docs/Implementation%20Plan.md).

See the [repository README](../../README.md#local-development) for setup instructions (Docker Compose or running natively).

## Layout

```
app/
  core/       Settings, DB session, logging, standard response envelope,
              Redis client, rate limiting, audit log, S3/MinIO storage
  modules/    One package per business domain. `auth`, `customers`
              (Phase 1), `catalog`, `inventory` (Phase 2), `cart`
              (Phase 4), and `orders`, `payments` (Phase 5) have real
              endpoints. The rest (shipping, cms, admin, notifications)
              still expose a scaffold placeholder router; real endpoints
              land as each module's implementation phase begins.
  api/v1/     Aggregates all module routers under /api/v1
migrations/   Alembic, wired to app.core.database.Base.metadata
scripts/      One-off CLI scripts (e.g. bootstrapping the first admin user)
tests/
```

## Bootstrapping the first admin account

Staff account creation via API is Phase 7 (Admin Portal) work — until
then, create the first `super_admin` with:

```bash
python -m scripts.create_admin_user --email admin@example.com --role super_admin
```

## Known gotchas

- `bcrypt` is pinned to `4.0.1` in `requirements.txt`. `passlib==1.7.4`
  (last released 2020) version-sniffs `bcrypt.__about__`, which `bcrypt>=4.1`
  removed — hashing/verifying passwords raises a confusing "password cannot
  be longer than 72 bytes" error otherwise. Don't upgrade `bcrypt` alone.

## Scripts

```bash
ruff check .            # lint
ruff format --check .   # format check
pytest -q               # tests
alembic upgrade head    # apply migrations
alembic revision --autogenerate -m "message"   # new migration
```

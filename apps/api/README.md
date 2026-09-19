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
              (Phase 4), `orders`, `payments` (Phase 5), `shipping`
              (Phase 6), and `notifications`, `cms`, `admin`, `reports`
              (Phase 7) all have real endpoints. `notifications` is
              push-only (triggered by other modules; no dedicated
              router) and `reports` has no models.py — it only reads
              other modules' tables.
  api/v1/     Aggregates all module routers under /api/v1
migrations/   Alembic, wired to app.core.database.Base.metadata
scripts/      One-off CLI scripts (e.g. bootstrapping the first admin user)
tests/
```

## Bootstrapping the first admin account

`POST /admin/users` (Phase 7) creates staff accounts, but it requires
an already-authenticated `super_admin` — so the very first one must
still be bootstrapped via this CLI script:

```bash
python -m scripts.create_admin_user --email admin@example.com --role super_admin
```

## Backup & Restore (NFR-DR-001..003)

`scripts/backup_database.sh` and `scripts/restore_database.sh` wrap
`pg_dump`/`pg_restore` in custom format (compressed, dependency-order-
safe regardless of table order). Both read connection info from
`DATABASE_URL` (falling back to the local dev default), stripping the
`+asyncpg` driver suffix `pg_dump`/`pg_restore` don't understand.

Take a backup:

```bash
./scripts/backup_database.sh [output_dir]   # default: ./backups
```

Restore one (**destructive** — drops and recreates the `public` schema
first):

```bash
./scripts/restore_database.sh <backup_file>          # prompts for confirmation
./scripts/restore_database.sh <backup_file> --yes    # for scripted/CI use
```

Verify a backup by restoring it into a disposable database (never the
one you can't afford to lose) and confirming `alembic check` reports no
drift and the app boots against it — that's exactly the drill this was
tested with while building it: back up, drop the schema, restore,
confirm row counts and `alembic current` match pre-backup state.

In production this script should run on a schedule (cron, a CI
scheduled job, or your hosting platform's managed-Postgres backup
feature if it has one) with `output_dir` pointed at off-host storage —
a backup that lives on the same disk as the database it backs up
doesn't survive the failure modes that matter (disk loss, host
termination). Retention/off-host upload isn't implemented here since it
depends entirely on where this gets deployed.

## Observability

- **Metrics**: `GET /metrics` exposes Prometheus text format —
  request-level metrics (latency, count by path/method/status) via
  `prometheus-fastapi-instrumentator`, plus business counters/gauges
  defined in `app/core/metrics.py` (`orders_placed_total`,
  `payment_webhook_results_total`, `notifications_failed_total`,
  `low_stock_variants`). `monitoring/prometheus-alerts.yml` has
  matching Prometheus alerting rules (payment failure rate, low stock,
  API error rate/latency) — not deployed anywhere in this repo, since
  there's no Prometheus/Alertmanager instance in these environments,
  but ready for a real deployment's Prometheus to load via
  `rule_files:`.
- **Errors**: set `SENTRY_DSN` to enable Sentry (`app/main.py` only
  calls `sentry_sdk.init()` when it's set).

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

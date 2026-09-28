# Setup Guide

Practical instructions for getting The Shatranj Heritage running locally — beyond the quick-start in the [README](../README.md). Covers every environment variable, bootstrapping an admin account, running the full test suite (including the new Playwright E2E suite), and the problems people actually hit.

## Contents

- [Prerequisites](#prerequisites)
- [Option A — Full stack via Docker Compose](#option-a--full-stack-via-docker-compose)
- [Option B — Running apps natively (hot reload)](#option-b--running-apps-natively-hot-reload)
- [Environment variables](#environment-variables)
- [Bootstrapping an admin account](#bootstrapping-an-admin-account)
- [Seeded RBAC roles](#seeded-rbac-roles)
- [Payment & courier providers: fake vs. real](#payment--courier-providers-fake-vs-real)
- [Notifications in dev](#notifications-in-dev)
- [Running tests](#running-tests)
- [Playwright end-to-end suite](#playwright-end-to-end-suite)
- [Localization (English/Bangla)](#localization-englishbangla)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Docker** and **Docker Compose**, for the all-in-one path, **or**
- **Python 3.11+** and **Node.js 22+**, for running the apps natively (faster inner loop, hot reload)

Either way you'll want `git` and a terminal. No other local services are required — Postgres, Redis, and MinIO (S3-compatible object storage) all run in containers under either path.

## Option A — Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

This brings up five services: `postgres`, `redis`, `minio` (+ a one-off `minio-init` that creates the object storage bucket), `api` (`http://localhost:8000`), and `web` (`http://localhost:3000`).

**The `api` container does not run migrations on startup.** Run them yourself after the first `up` (and again any time you pull new migrations):

```bash
docker compose exec api alembic upgrade head
```

Then [bootstrap an admin account](#bootstrapping-an-admin-account) before trying to sign in to `/admin/login`.

To stop everything: `docker compose down`. Add `-v` to also drop the Postgres/MinIO volumes (full reset — you'll need to re-migrate and re-bootstrap the admin afterward).

## Option B — Running apps natively (hot reload)

Start just the infrastructure containers, then run each app directly on your machine:

```bash
docker compose up postgres redis minio minio-init
```

**API:**

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python -m scripts.create_admin_user --email admin@example.com --role super_admin   # see below
uvicorn app.main:app --reload
```

**Web** (separate terminal):

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

The API listens on `:8000`, the web app on `:3000`. If you started the infrastructure containers with different host ports than the defaults, update `apps/api/.env` (`DATABASE_URL`, `REDIS_URL`, `S3_ENDPOINT_URL`) to match.

## Environment variables

### Root `.env` (consumed by `docker-compose.yml`)

| Variable | Default | Notes |
| --- | --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `shatranj` / `shatranj` / `shatranj_heritage` | Passed through to the `postgres` container and used to build `DATABASE_URL` for the `api` container |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | `minioadmin` / `minioadmin` | MinIO root credentials |
| `S3_BUCKET_NAME` | `shatranj-heritage` | Bucket `minio-init` creates and makes public-readable |
| `JWT_SECRET_KEY` | `change-me-in-every-environment` | Must be changed for anything beyond local dev — the API refuses to boot in production with this literal placeholder value |
| `SENTRY_DSN` | empty | Leave empty locally; error tracking is a no-op without it |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Passed to the `web` container; must be reachable from the **browser**, not just from other containers |
| `NEXT_PUBLIC_ASSET_BASE_URL` | `http://localhost:9000` | Same constraint — must resolve from the browser. Used by `next.config.ts` to allowlist the image host for `next/image`'s optimizer |

### `apps/api/.env` (native runs; docker-compose overrides `DATABASE_URL`/`REDIS_URL`/`S3_ENDPOINT_URL` itself)

| Variable | Default | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Set to `production` to trigger the startup safety check (refuses to boot with placeholder secrets) |
| `DEBUG` | `true` | When true, `POST /auth/forgot-password` echoes the reset token directly in its response body — see [Notifications in dev](#notifications-in-dev) |
| `CORS_ALLOW_ORIGINS` | `["http://localhost:3000"]` | JSON array; add any other origin the web app is served from |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | Where payment-gateway redirects (success/fail/cancel) land — **not** this API |
| `DATABASE_URL` | `postgresql+asyncpg://shatranj:shatranj@localhost:5432/shatranj_heritage` | |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET_NAME` | see `.env.example` | MinIO connection |
| `JWT_SECRET_KEY` / `JWT_ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | see `.env.example` | |
| `PAYMENT_PROVIDER` | `sslcommerz` | Set to `fake` for local dev/testing without hitting a real gateway — see [below](#payment--courier-providers-fake-vs-real) |
| `SSLCOMMERZ_STORE_ID` / `SSLCOMMERZ_STORE_PASSWORD` / `SSLCOMMERZ_API_BASE_URL` / `SSLCOMMERZ_IS_LIVE` | `testbox` / `qwerty` / `https://sandbox.sslcommerz.com` / `false` | SSLCommerz's own public sandbox credentials — only relevant when `PAYMENT_PROVIDER=sslcommerz` |
| `PAYMENT_WEBHOOK_SECRET` | `change-me-in-every-environment` | Signs/verifies the payment webhook |
| `COURIER_PROVIDER` | `pathao` | Set to `fake` to avoid needing real Pathao credentials — see below |
| `PATHAO_API_BASE_URL` / `PATHAO_CLIENT_ID` / `PATHAO_CLIENT_SECRET` | see `.env.example` | Only relevant when `COURIER_PROVIDER=pathao`; the placeholder client id/secret will not authenticate against Pathao's real API |
| `SENTRY_DSN` | empty | |
| `LOG_LEVEL` | `INFO` | |

### `apps/web/.env.local` (native runs)

| Variable | Default | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | |

`NEXT_PUBLIC_ASSET_BASE_URL` isn't in `apps/web/.env.example` because its code default (`http://localhost:9000`) already matches MinIO's default port — only set it if you've moved MinIO elsewhere.

## Bootstrapping an admin account

Staff/admin accounts aren't self-service (by design — see the script's own docstring). Create the first one with:

```bash
cd apps/api   # so `app` resolves as a package
python -m scripts.create_admin_user --email admin@example.com --role super_admin
```

It prompts for a password interactively (recommended). For scripted/CI use, `--password` is accepted directly — avoid that in a shell with shared history. Run it again with a different `--email`/`--role` to create additional staff accounts for testing role-based access, or use the Admin Portal's own Staff & Roles page once you're signed in with the first one.

Sign in at `http://localhost:3000/admin/login`.

## Seeded RBAC roles

The RBAC seed migration creates six roles with fixed permission sets:

| Role | Scope |
| --- | --- |
| `super_admin` | Full administrative access |
| `inventory_manager` | Products, variants, stock levels |
| `content_manager` | Categories, CMS pages, blog posts, reviews |
| `marketing_manager` | Coupons, campaigns, promotions |
| `order_manager` | Orders, shipments, refunds |
| `customer_support` | Read access to customer accounts |

`GET /api/v1/admin/roles` (or the Admin Portal's Staff & Roles → Roles & Permissions tab) lists each role's exact permission codes.

## Payment & courier providers: fake vs. real

Both `PaymentProvider` and `CourierProvider` are interfaces with a real implementation (`SSLCommerzProvider`, `PathaoCourierProvider`) and a fake one used by the automated test suite. For local development:

- **`PAYMENT_PROVIDER=fake`** — checkout with any online method (bKash/Nagad/Rocket/card) completes instantly with no external call and no redirect. Cash on delivery (`cod`) never touches this provider regardless of the setting.
- **`PAYMENT_PROVIDER=sslcommerz`** (default) — real calls to SSLCommerz's public sandbox using the default `testbox`/`qwerty` credentials baked into `.env.example`. This works out of the box for manual testing of the actual redirect flow, but needs network access to `sandbox.sslcommerz.com`.
- **`COURIER_PROVIDER=fake`** — admin courier assignment succeeds instantly with a synthetic tracking number.
- **`COURIER_PROVIDER=pathao`** (default) — the placeholder `PATHAO_CLIENT_ID`/`PATHAO_CLIENT_SECRET` in `.env.example` will **not** authenticate against Pathao's real API. Either request real sandbox credentials from Pathao or leave this on `fake` for local work.

The Playwright E2E suite only exercises Cash on Delivery, so neither setting affects it.

## Notifications in dev

There is no real email/SMS provider wired up (see the README's Known limitations) — `NotificationChannel`'s only implementation logs to the `notifications_log` table. Two dev-mode conveniences compensate for this during manual testing:

- With `DEBUG=true` (the default), `POST /auth/forgot-password` echoes the reset token directly in its JSON response, and the storefront's `/forgot-password` page surfaces it under a "Dev mode" hint so you can complete the reset flow without a real inbox.
- To see what would have been sent otherwise, query `notifications_log` directly or use the Admin Portal's Audit Log viewer.

## Running tests

**Backend** (from `apps/api`, with the venv active, Postgres and Redis running):

```bash
ruff check .
ruff format --check .
alembic upgrade head   # tests run against a real Postgres
pytest -q
```

**Frontend** (from `apps/web`):

```bash
npm run lint
npm run typecheck
npm run format
npm run build
```

## Playwright end-to-end suite

`apps/web/tests/e2e/` covers four golden paths against a fully running stack: guest checkout, logged-in checkout, admin product creation, and admin order fulfillment. Each spec is self-sufficient — it creates its own test product/category via the admin API rather than depending on whatever happens to already be in your database.

```bash
cd apps/web
npx playwright install --with-deps chromium   # first run only
npm run test:e2e
```

Requires the full stack up (API on `:8000`, web on `:3000`) and an admin account — by default it uses `f7-super@example.com` / `Passw0rd1234`; override with `ADMIN_E2E_EMAIL`/`ADMIN_E2E_PASSWORD` env vars if you [bootstrapped](#bootstrapping-an-admin-account) a different one. `PLAYWRIGHT_BASE_URL` and `PLAYWRIGHT_API_URL` override the web/API URLs if you're not using the defaults.

The admin login endpoint is rate-limited (10 requests/60s) as a brute-force guard — a real security feature, not a bug. Re-running the suite back-to-back several times in a short window can trip it; the tests will fail with `RATE_LIMITED` if so. Wait a minute and retry, or open a fresh admin session and reuse its token.

This suite also runs in CI as the `e2e` job in `.github/workflows/ci.yml`, which spins up Postgres/Redis, bootstraps its own throwaway admin, builds and serves both apps, then runs the suite — see that file for the exact sequence if you need to reproduce it locally.

## Localization (English/Bangla)

The storefront (not the Admin Portal, which is deliberately English-only) is fully localized. The locale switcher lives in the storefront nav and persists to `localStorage` under `shatranj_locale`. To manually QA the Bangla UI, switch locale in the nav and re-check a page — no server restart needed, it's all client-side.

## Troubleshooting

**"Could not connect to Redis" / `pg_isready` fails on a fresh container.** If you're not using Docker Compose for infra, make sure Postgres and Redis are actually running (`service postgresql start`, `service redis-server start` on a bare Linux box) before starting the API.

**Images don't load / 500 from `/_next/image`.** Next.js's image optimizer blocks loopback/private-IP hosts by default (a real SSRF protection, not a bug). `next.config.ts` already allows this for local dev when `NEXT_PUBLIC_ASSET_BASE_URL` resolves to `localhost`/a private IP. If images still fail with a `500` (not a `400`), check that MinIO is actually running and the bucket exists — that's an environment problem, not a config one.

**`429 RATE_LIMITED` while testing login/register/checkout by hand.** Several endpoints (login, register, forgot-password, reset-password, order placement) are rate-limited per the SRS's security requirements. This is expected under rapid manual re-testing or repeated E2E runs — wait for the window to clear (most are 10 requests/60s).

**A staff account can't do something you expect.** Check its roles via the Admin Portal's Staff & Roles page or `GET /admin/roles`, against the [seeded roles table](#seeded-rbac-roles) above. A `super_admin` account can't remove its own `staff.manage` permission via self-role-reassignment — this is an intentional guard against accidental self-lockout, not a bug.

**Migrations "already exist" or admin bootstrap says the email exists.** Both Postgres and MinIO data persist in named Docker volumes (`postgres_data`, `minio_data`) across `docker compose down`/`up` cycles. If you want a truly clean slate, `docker compose down -v` first.

**CI's `e2e` job fails but everything works locally.** Check `.github/workflows/ci.yml`'s `e2e` job logs for the API/web server startup logs (uploaded as artifacts on failure) — a real server-startup problem (e.g. a migration that fails against a fresh database) will surface there before any Playwright test even runs.

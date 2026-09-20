# Deployment Runbook

Phase 8 (Hardening & MVP Launch Readiness) deliverable: the staging →
production deployment procedure, rollback plan, and deploy strategy on
top of the Docker images and CI pipeline built in Phase 0
(`apps/api/Dockerfile`, `apps/web/Dockerfile`, `.github/workflows/ci.yml`).

Per [Software Requirements Specification.md §10](Software%20Requirements%20Specification.md)
("Deployment Strategy"), this stays cloud-provider-agnostic: "cloud
deployment" is a hosting decision for whoever operates this, not
something this repo hardcodes. What follows applies regardless of
which host runs the containers. Kubernetes is explicitly marked
"future" in the SRS's own architecture table, so the deploy strategy
below is built from what Phase 0 already shipped — Docker images and
Docker Compose — not from infrastructure this repo doesn't have.

## Environments

| Environment | Purpose | Data |
| --- | --- | --- |
| Development | Local, `docker-compose.yml`, seed data, fake payment/courier providers | Disposable |
| Staging | Production-like; UAT, performance, and security testing before every release (SRS §10) | Realistic but non-production data |
| Production | Live traffic | Real customer/order data — backups mandatory (see `apps/api/README.md#backup--restore`) |

**Build once, promote the same artifact.** CI builds and tests exactly
one image per app per commit; staging and production run that same
image with different environment variables, never a rebuild from the
same source at a later time. This is what makes "staging passed" mean
anything for production.

## Pre-deploy checklist

Before promoting a build to staging or production:

1. CI is green on the commit being deployed (`ci.yml`: lint, format
   check, full test suite against real Postgres/Redis, migrations
   apply cleanly, OpenAPI schema exports).
2. `alembic upgrade head` has been reviewed for the migrations this
   release adds — confirm they're additive (new tables/columns/indexes)
   rather than destructive (dropped columns/tables), per the rollback
   note below. Every migration shipped through Phase 7 has been
   additive; keep it that way deliberately.
3. A fresh backup of the target database exists
   (`./scripts/backup_database.sh`) — non-negotiable for production,
   recommended for staging.
4. Required secrets are set for the target environment and are **not**
   the sample values `app/core/config.py` ships with — `Settings`
   itself refuses to boot with `ENVIRONMENT=production` and a
   placeholder `jwt_secret_key`/`payment_webhook_secret`/etc. left in
   place (Phase 8 security hardening), so a forgotten override fails
   loudly at startup instead of silently running insecure.

## Deploy procedure

1. **Build & tag.** CI builds `apps/api` and `apps/web` images tagged
   with the commit SHA (and `latest` for the default branch, if the
   registry setup wants that). Push both to whatever container
   registry the target host pulls from.
2. **Migrate first.** Run `alembic upgrade head` against the target
   database *before* rolling out the new API image. Every migration in
   this codebase is additive (new tables/columns/indexes, not drops),
   so the currently-running (old) API image continues to work
   unmodified against the post-migration schema — this ordering is
   what makes a rolling deploy safe instead of requiring downtime.
3. **Roll the API.** Replace API containers one at a time (or one
   batch at a time) behind a load balancer/reverse proxy, waiting for
   each replacement container to pass `GET /health` before sending it
   traffic and stopping the old one. With a single `api` container (as
   `docker-compose.yml` runs today), this degrades to brief downtime
   during the swap — running 2+ replicas behind a reverse proxy
   (nginx/Caddy/your host's load balancer) is what turns this into a
   true rolling deploy with zero downtime; docker-compose.yml as
   checked in is a local-dev config, not this production topology.
4. **Roll the web app.** Same pattern, after the API is confirmed
   healthy on the new version (the web app calls the API; deploying it
   first against an old API risks a version mismatch in either
   direction, so API-then-web is the safe order).
5. **Smoke test.** Hit `/health`, `/metrics`, and a couple of read
   endpoints (`GET /api/v1/products`, `GET /api/v1/content/pages`)
   against the newly deployed version. For a production release,
   also place a real end-to-end test order using a payment gateway
   sandbox/test method before calling the deploy done.
6. **Watch.** Check `GET /metrics` and Sentry (if `SENTRY_DSN` is set)
   for an elevated error rate or the `ApiServerErrorRateHigh` /
   `PaymentWebhookFailureRateHigh` conditions in
   `apps/api/monitoring/prometheus-alerts.yml` for at least the next
   15–30 minutes.

## Rollback plan

- **Application rollback (the common case):** redeploy the previous
  image tag through the same rolling procedure above. Since every
  migration to date is additive, the old API image keeps working
  correctly against the newer (post-migration) schema — no `alembic
  downgrade` needed for a bad application release, which is by far the
  safer path (a downgrade that drops a column/table is itself a
  destructive operation you'd be running under incident pressure).
- **Migration rollback (rare, higher-risk):** only needed if the
  migration itself is the problem (e.g. a bad index causing lock
  contention). Take a fresh backup first, then `alembic downgrade
  <previous revision>`. Never run a downgrade against production
  without having verified it against a restored backup copy of
  production data first — the same drill as
  `apps/api/README.md#backup--restore`.
- **Full disaster recovery:** restore the most recent backup via
  `./scripts/restore_database.sh` (see `apps/api/README.md` for the
  full drill, verified end-to-end during Phase 8: backup, wipe, restore,
  confirm row counts and `alembic check` match).

## Staging → production promotion gate

Per SRS §10/§11: a build is promoted from staging to production only
after, on that exact build:

- UAT sign-off against the MVP feature summary (see
  `UAT Checklist.md` in this directory).
- No unresolved critical/high-severity defects.
- Performance targets from SRS Part 4 (public pages <2s, API reads
  <500ms, checkout <2s, search <1s) hold under a staging load test.
- Security review findings from Phase 8 are closed (see the Phase 8
  commit history for what was found and fixed).

# The Shatranj Heritage

**Bangladesh's first dedicated e-commerce platform for chess.**

Chess has grown steadily in Bangladesh over the past decade, but the market for chess equipment, books, and handcrafted sets remains scattered across general marketplaces, informal importers, and a handful of physical shops. The Shatranj Heritage exists to fix that: a specialized platform that brings commerce, community, craftsmanship, and education together for players, collectors, schools, clubs, tournament organizers, and local artisans.

## Vision

> To become the most trusted and inspiring destination for chess enthusiasts by connecting players, artisans, educators, and organizations through a unified commerce and community platform that celebrates the culture of chess.

Beyond selling products, the platform is built to showcase Bangladeshi craftsmanship, give local artisans national (and eventually international) visibility, and strengthen the country's chess community — with an ambition to grow into the leading chess commerce ecosystem across South Asia.

## Who it's for

- **Casual & competitive players** — from beginners buying their first set to tournament players needing FIDE-standard boards, clocks, and equipment
- **Collectors** — premium wooden, marble, and brass sets, limited editions, artistic pieces
- **Gift buyers** — personalized and corporate chess gifts
- **Schools, academies, clubs & tournament organizers** — bulk and institutional procurement
- **Local artisans** — a digital storefront and nationwide reach for handcrafted chess products

## Project status

**The V1 (MVP) build is feature-complete: backend Phases 0–8 and frontend Phases F0–F9 are both done**, per the [Implementation Plan](docs/Implementation%20Plan.md) and [Frontend Implementation Plan](docs/Frontend%20Implementation%20Plan.md). What's left before a real launch is stakeholder UAT, production credentials, and the items under [Known limitations](#known-limitations) below — not further engineering on the MVP scope itself.

### Backend (Phases 0–8)

- **Phase 0 (engineering foundations)** — done: monorepo, FastAPI + Next.js skeletons, Docker Compose, CI, linting/formatting.
- **Phase 1 (Authentication & Customers)** — done: customer registration/login/logout/refresh/forgot-reset-password, admin login, RBAC (roles/permissions), customer profile & address management (self-service and admin).
- **Phase 2 (Product Catalog & Inventory)** — done: categories (tree, self-referencing), artisans, products & variants with attribute-based filtering, image uploads to S3-compatible storage, public browse/search/filter/sort, and admin inventory management (stock adjustment with a full audit ledger, low-stock reporting).
- **Phase 3 (Search & Discovery)** — done: Postgres full-text search (weighted, GIN-indexed `tsvector` over product name/description) with relevance ranking, SKU matching, a `featured` filter and flag, and a no-results state that surfaces category and featured-product suggestions instead of a dead end.
- **Phase 4 (Shopping Cart)** — done: guest (cookie-based) and customer (token-based) carts, add/update/remove items with quantity capped by live inventory, a standalone totals/pricing service, self-healing stock revalidation, and a guest cart that merges into the customer's own cart on login/registration.
- **Phase 5 (Checkout, Payments & Orders)** — done: checkout quote and atomic order placement (guest or customer, row-locked inventory reservation, idempotency-key replay protection), a `PaymentProvider` interface with a real SSLCommerz integration and a fake one for tests, a signature-verified payment webhook, the full order lifecycle (pending → awaiting payment → confirmed → packed → shipped → delivered, with cancellation restoring stock and auto-filing a refund request), and admin order management with audit-logged status transitions.
- **Phase 6 (Shipping & Fulfillment)** — done: real location- and weight-based shipping cost (admin-configurable rate table) wired into checkout quote and order placement, a `CourierProvider` interface with a real Pathao integration and a fake one for tests, admin courier assignment, and shipment tracking through to delivery.
- **Phase 7 (Notifications, Admin Portal APIs & Reporting)** — done: a notification service (behind a `NotificationChannel` interface) triggered by registration, password reset, order/payment confirmation, and shipment events; CMS-lite policy pages with an admin publish/unpublish workflow; admin staff account creation and role assignment, an audit log viewer, admin-configurable shipping rates; and six admin reporting endpoints backed by real SQL aggregations. The Admin Portal *UI* for all of this shipped in Frontend Phases F5–F8, below.
- **Phase 8 (Hardening & MVP Launch Readiness)** — done, scoped to what's real engineering work rather than infrastructure/process this repo can't provide: a security pass, a performance pass, a reliability pass (concurrency test proving five simultaneous checkouts racing for the last unit of stock never oversell), Prometheus metrics with alert rules, tested backup/restore tooling, a deployment runbook and a UAT checklist. **Not done, because it genuinely can't be from inside this environment:** UAT itself (requires real stakeholders — the checklist is the substitute deliverable) and live Grafana dashboards/Alertmanager routing (no instance exists here — the metrics and alert rules are ready for one).

### Frontend (Phases F0–F9)

- **F0 (Foundations)** — design tokens, shared UI primitives (Button, Field, Table, Modal, etc.), i18n scaffold (English/Bangla).
- **F1 (Homepage & Marketing)** — homepage, legal/policy pages, newsletter signup.
- **F2 (Catalog, Search & Discovery)** — product listing with filters, category pages, product detail with variants, search.
- **F3 (Cart & Checkout)** — cart page, multi-step checkout (address/shipping/payment/review), order confirmation.
- **F4 (Order Tracking & Account)** — account tabs (profile/addresses/orders), order detail with shipment tracking, cancellation, and payment retry.
- **F5–F8 (Admin Portal)** — the full operational UI the Phase 7 backend APIs were waiting on: auth-gated shell and dashboard; product/variant/image/category/CMS management; orders, shipping, customers, staff & roles, settings, and a filterable audit log; a reporting & analytics dashboard (Recharts).
- **F9 (Cross-Cutting Hardening & Launch QA)** — accessibility (focus management, live regions, ARIA on tabs/dialogs/forms, keyboard-reachable everything), full English/Bangla coverage of the storefront, responsive QA (phone-width storefront, tablet-width admin), `next/image` performance pass, and a Playwright end-to-end suite covering the golden paths (guest checkout, logged-in checkout, admin product creation, admin order fulfillment) wired into CI.

See [`docs/Setup Guide.md`](docs/Setup%20Guide.md) to run all of this locally, and [`docs/UAT Checklist.md`](docs/UAT%20Checklist.md) for the launch-readiness checklist (now fully mapped to real pages, not API-only steps).

### Known limitations

Real gaps, not just "not started yet" — worth knowing before treating this as launch-ready:

- **Notifications don't actually send.** The only `NotificationChannel` implementation logs to the database (`notifications_log`); there's no real SMTP/SendGrid/Twilio wiring. Customers never receive a real registration, password-reset, or order-confirmation email/SMS today.
- **No persistent guest order tracking.** A guest's only order-status view is the confirmation page shown once, right after checkout. There's no emailed link or standalone "track my order" page to return to later.
- **`best_selling` product sort is a stub** (falls back to newest); there's no `rating` sort since Reviews (V2) doesn't exist yet.
- **Payment/courier integrations are untested against live services.** `SSLCommerzProvider` and `PathaoCourierProvider` are real implementations, but every automated test runs against their `fake` counterparts (`PAYMENT_PROVIDER=fake` / `COURIER_PROVIDER=fake`) — nobody has round-tripped a real sandbox call from this codebase yet.
- **No live monitoring stack.** Prometheus metrics and alert rules are correct and ready, but no Grafana/Alertmanager instance exists to point them at.
- Wishlist, Reviews & Ratings, and a Loyalty Program are explicitly **V2 backlog** (see Roadmap below), not MVP gaps.

## Documentation

Full product and engineering requirements live in [`docs/`](docs/):

| Document | Purpose |
| --- | --- |
| [Product Vision Document](docs/Product%20Vision%20Document.md) | Why the product exists, target audience, vision & mission |
| [Business Requirements Document](docs/Business%20Requirements%20Document.md) | Business goals, capabilities, rules, and constraints |
| [Software Requirements Specification](docs/Software%20Requirements%20Specification.md) | Functional & non-functional requirements, architecture, data model, API design |
| [Product Backlog & User Stories](docs/Product%20Backlog%20and%20User%20Stories.md) | Epics, user stories, and MVP scope for implementation |
| [Entity Relationship Diagram & Database Schema](docs/Entity%20Relationship%20Diagram%20and%20Database%20Schema.md) | ERD and field-level PostgreSQL schema, ready for migrations |
| [API Specification](docs/API%20Specification.md) | REST endpoint contract, conventions, and request/response shapes |
| [Implementation Plan](docs/Implementation%20Plan.md) | Phased, sequenced backend engineering plan from empty repo to MVP launch and beyond |
| [Frontend Implementation Plan](docs/Frontend%20Implementation%20Plan.md) | Phased Next.js frontend plan (storefront + Admin Portal) built against the backend above |
| [Deployment Runbook](docs/Deployment%20Runbook.md) | Staging→production promotion, rollback, and on-call procedures |
| [UAT Checklist](docs/UAT%20Checklist.md) | Launch-readiness checklist mapped to real pages/endpoints, for a stakeholder to run |
| [Setup Guide](docs/Setup%20Guide.md) | Practical local dev setup: environment variables, running the stack, tests, and troubleshooting |

## Planned technology stack

As proposed in the SRS, pending final confirmation:

| Layer | Choice |
| --- | --- |
| Frontend | Next.js (React + TypeScript) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| Search | PostgreSQL Full-Text Search (MVP), Elasticsearch/OpenSearch later if needed |
| Object Storage | S3-compatible storage |
| Auth | JWT + Refresh Tokens |
| Payments | SSLCommerz (bKash, Nagad, Rocket, cards), Cash on Delivery |
| Deployment | Docker, GitHub Actions CI/CD |
| Monitoring | Prometheus + Grafana |

The initial architecture is a **modular monolith** rather than microservices, to keep MVP delivery fast and simple while preserving clean module boundaries for future extraction.

## Repository layout

```
apps/
  api/          FastAPI backend — modular monolith (app/modules/<domain>/...)
  web/          Next.js (App Router, TypeScript) frontend — storefront + Admin Portal
  web/tests/e2e Playwright golden-path end-to-end suite
docs/    Product & engineering requirements (PVD, BRD, SRS, ERD, API spec, implementation plans, setup guide)
docker-compose.yml   Local dev environment: Postgres, Redis, MinIO, API, web
```

## Local development

**Prerequisites:** Docker, or Python 3.11+ and Node.js 22+ for running the apps outside containers.

This section is the quick version — for environment variable reference, bootstrapping an admin account, running the Playwright suite, and troubleshooting, see the **[Setup Guide](docs/Setup%20Guide.md)**.

### Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build

# First run only (or after pulling new migrations) — the api
# container does not run these automatically on startup:
docker compose exec api alembic upgrade head
```

This starts Postgres, Redis, MinIO, the API (`http://localhost:8000`), and the web app (`http://localhost:3000`). A one-off `minio-init` service creates the object storage bucket on first run.

### Running apps directly (faster inner loop, hot reload)

Start just the infrastructure with Docker, then run each app natively:

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
uvicorn app.main:app --reload
```

**Web:**

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

### Checks

```bash
# API — from apps/api, with the venv active
ruff check . && ruff format --check . && pytest -q

# Web — from apps/web
npm run lint && npm run typecheck && npm run format && npm run build

# Web E2E (golden paths) — from apps/web, full stack already running
npx playwright install --with-deps chromium   # first run only
npm run test:e2e
```

Optionally install [pre-commit](https://pre-commit.com/) hooks (`pre-commit install`) to run the same checks automatically before each commit.

## Roadmap

- **V1 (MVP)** — Product catalog, search, cart, checkout, payments, order management, inventory, admin dashboard. **Built and feature-complete** (see Project status above); what remains is UAT, production credentials, and the [Known limitations](#known-limitations).
- **V2** — Wishlist, reviews & ratings, coupons, blogs & buying guides, richer CMS
- **V3** — Multi-vendor marketplace for artisans, mobile apps, AI-powered recommendations, regional (South Asia) expansion

## License

Not yet decided.

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

Engineering implementation is underway, following the [Implementation Plan](docs/Implementation%20Plan.md).

- **Phase 0 (engineering foundations)** — done: monorepo, FastAPI + Next.js skeletons, Docker Compose, CI, linting/formatting.
- **Phase 1 (Authentication & Customers)** — done: customer registration/login/logout/refresh/forgot-reset-password, admin login, RBAC (roles/permissions), customer profile & address management (self-service and admin), all wired end-to-end through a working Next.js UI.
- **Phase 2 (Product Catalog & Inventory)** — done: categories (tree, self-referencing), artisans, products & variants with attribute-based filtering, image uploads to S3-compatible storage, public browse/search/filter/sort, and admin inventory management (stock adjustment with a full audit ledger, low-stock reporting).
- **Phase 3 (Search & Discovery)** — done: Postgres full-text search (weighted, GIN-indexed `tsvector` over product name/description) with relevance ranking, SKU matching, a `featured` filter and flag, and a no-results state that surfaces category and featured-product suggestions instead of a dead end.
- **Phase 4 (Shopping Cart)** — done: guest (cookie-based) and customer (token-based) carts, add/update/remove items with quantity capped by live inventory, a standalone totals/pricing service (subtotal plus shipping/tax/discount placeholders Checkout will fill in later), self-healing stock revalidation, and a guest cart that merges into the customer's own cart on login/registration.
- **Phase 5 (Checkout, Payments & Orders)** — done: checkout quote and atomic order placement (guest or customer, row-locked inventory reservation, idempotency-key replay protection), a `PaymentProvider` interface with a real SSLCommerz integration and a fake one for tests, a signature-verified payment webhook that converts a reservation into a real deduction on success, the full order lifecycle (pending → awaiting payment → confirmed → packed → shipped → delivered, with cancellation restoring stock and auto-filing a refund request), and admin order management with audit-logged status transitions.
- **Phase 6 (Shipping & Fulfillment)** — done: real location- and weight-based shipping cost (admin-configurable rate table, replacing Phase 5's flat placeholder) wired into checkout quote and order placement, a `CourierProvider` interface with a real Pathao integration and a fake one for tests, admin courier assignment (manual tracking number or provider-booked) that moves a packed order to shipped, and shipment tracking through to a delivery confirmation that completes the order.

Next up: Phase 7 (Notifications, Admin Portal & Reporting).

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
| [Implementation Plan](docs/Implementation%20Plan.md) | Phased, sequenced engineering plan from empty repo to MVP launch and beyond |

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
  api/   FastAPI backend — modular monolith (app/modules/<domain>/...)
  web/   Next.js (App Router, TypeScript) frontend
docs/    Product & engineering requirements (PVD, BRD, SRS, ERD, API spec, implementation plan)
docker-compose.yml   Local dev environment: Postgres, Redis, MinIO, API, web
```

## Local development

**Prerequisites:** Docker, or Python 3.11+ and Node.js 22+ for running the apps outside containers.

### Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build
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
```

Optionally install [pre-commit](https://pre-commit.com/) hooks (`pre-commit install`) to run the same checks automatically before each commit.

## Roadmap

- **V1 (MVP)** — Product catalog, search, cart, checkout, payments, order management, inventory, admin dashboard
- **V2** — Wishlist, reviews & ratings, coupons, blogs & buying guides, richer CMS
- **V3** — Multi-vendor marketplace for artisans, mobile apps, AI-powered recommendations, regional (South Asia) expansion

## License

Not yet decided.

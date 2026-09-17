# Implementation Plan

**Project Name:** The Shatranj Heritage
**Document Version:** 1.0 (Draft)
**Document Owner:** Engineering
**Status:** Draft
**Last Updated:** September 2026

---

## 1. Purpose

This document translates the Product Vision, Business Requirements Document (BRD), Software Requirements Specification (SRS), Entity Relationship Diagram & Database Schema, API Specification, and Product Backlog into a **sequenced, buildable engineering plan**.

Where those documents define *what* the platform is and *why* it exists, this plan defines **the order in which it gets built, by whom, against what exit criteria, and how the codebase evolves from an empty repository to a production MVP and beyond.**

It is intended to be the working reference for sprint planning once implementation begins. No application code exists yet — this plan starts from a clean repository.

---

## 2. Guiding Constraints From Prior Documents

These decisions are already made and this plan does not revisit them; it only sequences the work:

| Area | Decision | Source |
| --- | --- | --- |
| Architecture | Modular monolith (Auth, Catalog, Cart, Orders, Payments, Inventory, Shipping, CMS, Admin, Notifications as modules in one deployable) | SRS Part 1 §15, Part 3 §19 |
| Frontend | Next.js (React + TypeScript) | README, SRS |
| Backend | FastAPI (Python) | README, SRS |
| Database | PostgreSQL, UUID PKs, soft deletes, audit fields | ERD §2 |
| Cache | Redis | SRS Part 3 §14 |
| Search | Postgres full-text search (`tsvector`/GIN) for MVP; Elasticsearch/OpenSearch deferred | ERD §8, SRS Part 3 §11 |
| Object Storage | S3-compatible (MinIO in dev) | SRS Part 3 §10 |
| Auth | JWT access + refresh tokens, RBAC | SRS Part 3 §9 |
| Payments | SSLCommerz aggregating bKash/Nagad/Rocket/cards, plus Cash on Delivery | BRD, SRS Part 2 §9 |
| Deployment | Docker + GitHub Actions CI/CD; Kubernetes deferred | SRS, README |
| Monitoring | Prometheus + Grafana; Loki/OpenSearch for logs; Sentry for errors | SRS Part 1 §12 |
| Geography/Currency | Bangladesh only, BDT only, Bangla + English UI | BRD Part 2 §18 |
| DB migration order | `roles/permissions → admin_users → customers → categories/artisans → products → variants → inventory → carts → orders → payments/shipments → wishlists/reviews/cms (V2) → notifications_log/audit_logs` | ERD §7 |

The **module build order in this plan follows the functional dependency graph already defined in the BRD (Part 3 §9) and SRS (Part 2 §20)**: Auth → Catalog/Inventory → Cart → Checkout → Payment → Orders → Shipping → Reviews/Reporting, since each layer requires the one before it to exist.

---

## 3. Release Structure

Three releases, matching the BRD/Backlog roadmap, each broken into internal phases:

| Release | Theme | Epics Covered |
| --- | --- | --- |
| **V1 — MVP** | Curated online store: browse, buy, pay, fulfill, administer | EP-01 to EP-05, EP-07 to EP-10, EP-12 to EP-14, EP-17 |
| **V2 — Engagement** | Wishlist, reviews, promotions, richer CMS, refunds | EP-06, EP-11, EP-15, EP-16, plus deferred parts of EP-08/EP-09 |
| **V3 — Ecosystem** | Multi-vendor marketplace, mobile apps, AI, regional expansion | EP-18, mobile apps, AI search/recommendations |

This plan details **V1 in full phase-by-phase detail** (since that is the immediate execution target), and gives **V2/V3 as scoped follow-on phases** with less granularity, consistent with how far requirements have been specified in the SRS/backlog.

---

## 4. Phase Plan

Each phase lists: objective, scope, key technical work, and exit criteria (Definition of Done at the phase level, consistent with the backlog's DoD in §12 of the Product Backlog document). Durations are indicative sprint counts (assuming 2-week sprints, one small full-stack team of ~4-6 engineers); adjust to actual team size.

### Phase 0 — Engineering Foundations (Sprint 0, ~1–2 weeks)

**Objective:** Nothing product-specific is buildable until the repo can be run, tested, and deployed reproducibly.

**Scope:**
- Monorepo layout: `apps/web` (Next.js + TS), `apps/api` (FastAPI), `packages/` for shared types/config if needed.
- Local dev environment via Docker Compose: Postgres, Redis, MinIO, API, web.
- Base FastAPI app skeleton with module folders matching the domains in ERD §3 (`auth`, `catalog`, `inventory`, `cart`, `orders`, `payments`, `shipping`, `cms`, `admin`, `notifications`) — one Python package per module to preserve the "modular monolith, extractable later" decision.
- Alembic (or equivalent) migration tooling wired to the migration order in ERD §7.
- Base Next.js app skeleton with routing shell, design tokens, i18n scaffolding (Bangla/English) per NFR-LOC-001.
- Linting/formatting (ruff/black or equivalent for Python, ESLint/Prettier for TS), pre-commit hooks.
- GitHub Actions CI: lint, type-check, unit test, build, on every PR.
- Environment strategy: local, staging, production config via `.env` + secrets management (never committed).
- Error tracking (Sentry) and structured logging wired in from day one, even if empty — retrofitting logging later is expensive.
- Base `openapi.json` generation from FastAPI wired into CI so the API Specification doc can be checked for drift later.

**Exit criteria:** `docker compose up` boots API + web + DB + cache + storage; CI pipeline green on an empty "hello world" endpoint and page; a PR cannot merge without passing lint/type/test.

---

### Phase 1 — Identity, Customers & RBAC (EP-01, EP-02) — Auth Module (~3 sprints)

**Objective:** Every other module depends on knowing who the actor is (guest, customer, or admin with a role) — this must exist first, per the SRS functional dependency table (Auth ← Customer Management, mutual dependency resolved by building both together).

**Scope (backed by FR-AUTH-001..007, FR-CUS-001..005, US-AUTH-\*, US-CUS-\*):**
- `customers`, `customer_addresses`, `admin_users`, `roles`, `permissions`, `role_permissions`, `admin_user_roles` tables (ERD §5.1–5.3).
- Registration by email or mobile number (US-AUTH-001/002), password policy + hashing (NFR-SEC-004).
- Login (US-AUTH-003), JWT access + refresh token issuance/rotation (NFR-SEC-001).
- Forgot/reset password flow (US-AUTH-005/006).
- Logout / session invalidation (US-AUTH-007).
- RBAC middleware enforcing role/permission checks on FastAPI routes (Guest, Customer, Admin roles now; Inventory Manager, Content Manager, Marketing Manager, Customer Support, Super Admin roles scaffolded but populated as later phases need them).
- Customer profile CRUD, address book with default address (US-CUS-001..003).
- Order history endpoint stubbed (returns empty until Orders module exists in Phase 5) so the customer-facing UI shell can be built end-to-end early.
- Rate limiting on login/registration/password-reset endpoints (NFR-SEC-006).
- Auth audit logging (`audit_logs` table) for login/failed-login/role-change events (NFR-SEC-007).
- Auth endpoints per API Spec §3.1/§4 (`POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh`).

**Explicitly deferred:** email verification, mobile OTP verification, social login (US-AUTH-008/009/010 — Should/Won't for MVP).

**Exit criteria:** A customer can register, verify their session persists via refresh token, edit profile and addresses, and reset a forgotten password end-to-end through the actual UI. An admin user with a seeded Super Admin role can log into an (empty) admin shell. Auth test suite covers happy path + the abuse cases in NFR-SEC-005/006 (bad input, brute force, expired tokens).

---

### Phase 2 — Product Catalog & Inventory (EP-03, EP-14) (~3–4 sprints)

**Objective:** Nothing is sellable without a catalog and stock truth; per SRS dependency table, Catalog depends on Inventory (a product's purchasability is inventory-derived), so these are built together.

**Scope (FR-CAT-001..010, FR-INV-001..005, BR-PRO-\*, BR-INV-\*):**
- `categories` (self-referencing for hierarchy), `artisans`, `products`, `product_variants`, `product_images`, `inventory`, `inventory_transactions` (ERD §5.4–5.10).
- Admin CRUD for products/categories/variants (US-ADM-001/002), with SKU uniqueness enforcement (BR-PRO-001) and soft-delete/archive (BR-PRO rule: archived products excluded from search/listings).
- Multi-image upload to object storage with a primary-image concept (FR-CAT-004).
- Variant support (board size, wood type, finish, engraving) with attribute-based filtering (US-CAT-005).
- Artisan profile fields on products (FR-CAT-009) — this is the differentiator called out repeatedly in the BRD/PVD ("artisan storytelling"); treat it as first-class from the start rather than bolted on later.
- Inventory tracking: current/reserved/available quantities, reorder threshold, low-stock alert generation (US-INV-002), inventory adjustment endpoints with audit trail (US-INV-001/003).
- Public catalog read endpoints: list with pagination/filtering/sorting, product detail, category listing (API Spec §3.3).
- Related-products logic (simple same-category/attribute heuristic for MVP — no ML).
- Featured products / homepage curation fields (US-CAT-007).

**Exit criteria:** Admin can create a product with variants, images, and stock; a public visitor can browse categories, view a product detail page with accurate stock status (In Stock/Low Stock/Out of Stock per BR-INV-004), and out-of-stock items cannot be added to cart (validated in Phase 3, but the flag exists now).

---

### Phase 3 — Search & Discovery (EP-04) (~1–2 sprints, parallelizable with Phase 2's tail)

**Objective:** Layer discovery on top of the catalog once it has enough shape to search over.

**Scope (FR-SCH-001..007, US-SRC-001..003/005):**
- Postgres `tsvector`/GIN full-text index on product name + description (ERD §6 indexing strategy).
- Keyword search endpoint with relevance ranking (NFR-PER-003: results within 1s at MVP catalog scale).
- Filters: category, price range, material, availability (US-SRC-002) — combinable.
- Sorting: price asc/desc, newest, best-selling (best-selling requires order data, so this specific sort option is wired but returns "newest" fallback until Phase 5 exists, then backfilled), highest rated (stubbed until Reviews in V2), alphabetical.
- No-results state with suggested categories/featured products (US-SRC-005).

**Explicitly deferred:** autocomplete/search suggestions, recently viewed/searched (Should, V2), AI/semantic search (Could, V3).

**Exit criteria:** A visitor can search "wooden chess set", filter by price and material, and sort results, all within the NFR-PER-003 latency target on a seeded catalog of realistic size (hundreds of SKUs).

---

### Phase 4 — Shopping Cart (EP-05) (~1–2 sprints)

**Objective:** Bridge browsing and purchasing; depends on Catalog (Phase 2) per the SRS dependency table.

**Scope (FR-CRT-001..006, US-CRT-001..006/009):**
- `carts`, `cart_items` tables (ERD §5.11), scoped to session (guest) or customer (authenticated).
- Add/update/remove items, quantity capped by available inventory at add-time (US-CRT-002/009).
- Cart totals calculation service (subtotal, estimated shipping placeholder, estimated tax placeholder) — this service is reused unchanged by Checkout in Phase 6, so build it as a standalone pricing module now, not inline in a route handler.
- Cart summary and empty-cart UI states (US-CRT-004/005/006).
- Inventory re-validation before allowing checkout entry (US-CRT-009) — a hook point Checkout will call in Phase 6.

**Explicitly deferred:** save cart, persistent cross-device cart, cart expiration notices (Should/Could, V2/V3). Guest carts for MVP are session/cookie-based only.

**Exit criteria:** A guest and a logged-in customer can each build a cart, see accurate running totals, and get blocked from adding more than available stock.

---

### Phase 5 — Checkout, Payments & Orders (EP-07, EP-08, EP-09) (~4–5 sprints)

**Objective:** This is the commercial core of the MVP and the highest-risk phase (money + inventory correctness). It is deliberately scoped as one phase because Checkout, Payment, and Order creation must be built and tested together to satisfy the transactional-consistency requirements (NFR-REL-001..004).

**Scope (FR-CHK, FR-PAY-001..005, FR-ORD-001..007, US-CHK-\*, US-PAY-001..004, US-ORD-001..004):**
- `orders`, `order_items`, `payments`, `refunds` (stub), `shipments` (created here, populated in Phase 6) tables (ERD §5.12–5.14).
- Checkout flow: address selection (existing or new, US-CHK-002), shipping method selection (US-CHK-003, calculation rules stubbed pending Phase 6, using a flat/config-driven rate for MVP-in-progress), order review (US-CHK-004).
- **Order placement as a single atomic transaction**: validate inventory availability → reserve/deduct stock → create order + order_items → initiate payment → generate unique order number. This is the transaction referenced in SRS Part 3 §6 ("Transactions... Checkout, Payment, Inventory deduction") and must not partially succeed (NFR-REL-001).
- Payment integration: SSLCommerz integration behind a `PaymentProvider` interface (per SRS Part 3 §17 — "integrations isolated behind service interfaces... providers replaceable with minimal code changes") supporting bKash/Nagad/Rocket/cards through the aggregator, plus Cash on Delivery as a first-class payment method (order goes to "Awaiting Payment" per US-PAY-002).
- Payment webhook handler (`POST /payments/webhook/sslcommerz`) with signature verification, idempotent processing (a retried webhook must not double-apply), and reconciliation against `orders`/`payments` (NFR-REL-002/003, NFR-REL-001 "no duplicate orders from retries").
- Payment failure handling: no order left in a partially-charged or duplicated state; customer can retry (US-PAY-003).
- Order lifecycle state machine: Pending → Awaiting Payment → Confirmed → Packed → Shipped → Delivered, with Cancelled/Returned/Refunded as alternate terminal-ish states (BR-ORD-003), enforced server-side (e.g., cannot cancel a shipped order, per BR-ORD rule).
- Order cancellation with inventory restoration (US-ORD-003).
- Order tracking / order detail / order history endpoints (US-ORD-002/004, wired back into the Phase 1 stub).
- Admin order status transitions (`PATCH /admin/orders/{id}/status`) with audit logging.

**Explicitly deferred:** coupon application at checkout (US-CHK-005, V2 — the module is designed with a discount-amount field on the order so it's additive later, not a schema change), full refund workflow beyond recording (US-PAY-005, V2), returns (V2).

**Exit criteria:** A customer can complete a real end-to-end purchase (online payment and COD paths both) from cart through order confirmation, receives a unique order number, sees correct inventory deduction, and can cancel an unshipped order with stock restored. Load/failure testing confirms no duplicate orders under retried requests or webhook replays (this is a hard NFR-REL-001 gate, not a nice-to-have — write the test before considering the phase done).

---

### Phase 6 — Shipping & Fulfillment (EP-10) (~2 sprints)

**Objective:** Complete the order lifecycle with real logistics, replacing the flat-rate placeholder from Phase 5.

**Scope (FR-SHP-001..005, US-SHP-001..004):**
- Shipping cost calculation service driven by configurable business rules (location/weight/method per BR-SHP-002) — wired back into the Cart/Checkout pricing service built in Phase 4.
- Courier integration behind a `CourierProvider` interface (SRS names Pathao/RedX/SteadFast/Paperfly as examples) — implement one real provider for MVP launch, interface supports adding more without touching Order/Checkout code (BR-SHP-004, NFR-MNT-002).
- Shipment record creation, tracking number capture, delivery status updates (US-SHP-002/003).
- Delivery confirmation triggering the Delivered order status and customer notification (US-SHP-004, hands off to Phase 7's notification service).
- Failed delivery / return-shipment handling (basic, V2 refines fully).

**Exit criteria:** An admin/order-manager can assign a courier to a confirmed order, a tracking number surfaces to the customer, and delivery confirmation flips the order to Delivered and fires a notification.

---

### Phase 7 — Notifications, Admin Portal & Reporting (EP-12, EP-13, EP-17) (~3–4 sprints)

**Objective:** Give the business the operational surface to run the store, and close the loop on customer communication that every prior phase has been deferring to "Phase 7."

**Scope (FR-NOT-001..005, FR-ADM-001..007, FR-RPT-001..006, US-NOT-\*, US-ADM-\*, US-RPT-\*):**
- Notification service as an async job (background queue — Celery/RQ/arq or FastAPI background tasks backed by Redis, per SRS Part 3 §15 "background processing") with Email + SMS channels and templated messages for: registration, order confirmation, payment confirmation, shipping update, delivery confirmation, password reset.
- Retrofit every earlier phase's "notification TODO" (registration in Phase 1, order/payment/shipping/delivery in Phases 5–6) to call this service instead of stubs.
- Admin Portal (Next.js admin app or admin routes within the same app, role-gated): dashboard, product/category management UI (wrapping Phase 2 APIs), order management UI (wrapping Phase 5/6 APIs), customer management UI (wrapping Phase 1 APIs), user/role management UI, system settings (shipping rates, tax config), audit log viewer.
- Reporting: sales dashboard, revenue reports, inventory reports (slow-moving/low-stock), customer growth, product performance, refund reports — read-model queries against the transactional tables for MVP (a proper analytics/warehouse split is a V2+/scale concern per SRS Part 3 §2 "separation of transactional and analytical workloads", not required for launch volumes).
- Basic CMS needed to launch (homepage banners, policy pages — Terms, Privacy, Return, Shipping — required for NFR-COM-001 compliance even though full CMS is V2).

**Exit criteria:** All MVP customer touchpoints send the right notification at the right time; an operations person can run the entire order lifecycle, manage the catalog, and pull a sales/inventory report without touching the database directly; required legal/policy pages are live.

---

### Phase 8 — Hardening & MVP Launch Readiness (~2–3 sprints)

**Objective:** Everything functional exists by end of Phase 7; this phase is dedicated to the NFRs that cut across all modules and that are cheapest to fix now, before real traffic.

**Scope (mapped to SRS Part 4 NFRs):**
- Security pass: OWASP-Top-10 review of every endpoint (input validation, injection, XSS/CSRF where applicable — NFR-SEC-005), dependency vulnerability scan, secrets audit, rate limiting review across all public endpoints (not just auth).
- Performance pass against the explicit SRS targets: public pages <2s, product detail <3s, API reads <500ms, checkout <2s, search <1s (NFR-PER-001..004) — includes DB index verification against ERD §6, N+1 query audit, Redis caching of catalog/category/homepage reads (SRS Part 3 §14).
- Reliability pass: re-verify the Phase 5 transactional-consistency tests under concurrent load; verify inventory never goes negative (BR-INV rule) under race conditions (concurrent checkouts on last unit of stock).
- Accessibility pass to WCAG 2.1 AA where practical (NFR-USA-004/NFR-ACC), mobile-first responsive QA across the full customer journey (NFR-USA-003).
- Localization QA: full Bangla + English pass over customer-facing strings (NFR-LOC-001), BDT formatting consistency (NFR-LOC-002).
- Observability: Prometheus metrics + Grafana dashboards for orders/payments/inventory health (NFR-MON-001/003), alerting for payment failures and low stock (NFR-MON-002), Sentry error budgets set.
- Backup/DR: automated Postgres backups, documented restore procedure, tested at least once (NFR-DR-001..003).
- Staging → production deployment runbook, rollback plan, blue-green or rolling deploy strategy on the Docker/CI-CD pipeline built in Phase 0.
- UAT with real business stakeholders against the MVP feature summary (Product Backlog §14) before go-live.

**Exit criteria:** All Must-Have NFRs in SRS Part 4 §17 are demonstrably met (not just believed), a documented runbook exists for on-call, and UAT sign-off is obtained. **This is the MVP launch gate.**

---

## 5. V2 — Engagement Release (post-MVP)

Scoped at epic level per the backlog; detailed phase breakdown to happen once V1 ships and real usage data can inform priority within V2.

| Phase | Epics | Notes |
| --- | --- | --- |
| V2.1 — Wishlist & Reviews | EP-06, EP-11 | Reviews gated to verified purchasers (BR-ENG rule); moderation queue for admins. |
| V2.2 — Promotions | EP-15 | Coupon engine (percentage/fixed/seasonal), builds on the discount-amount field left in the Order schema during Phase 5. |
| V2.3 — Refunds & Returns | Deferred parts of EP-08/EP-09 | Full refund workflow, return request → inspection → refund/replacement (BRD return process). |
| V2.4 — CMS & Content | EP-16 | Blog, buying guides, richer landing pages — feeds the "Knowledge" product pillar from the PVD. |
| V2.5 — Institutional & Custom Orders | New (BRD Part 2 recommendations) | Quotation-based bulk procurement for schools/clubs, custom/engraved product requests — explicitly called out in the BRD as strategic differentiators worth prioritizing early in V2 even though not in the original MoSCoW MVP list. |

---

## 6. V3 — Ecosystem Release (future)

High-level only, per the depth already defined in source docs:

- **Vendor Marketplace (EP-18):** vendor registration/verification, vendor dashboard, product approval workflow, commission engine, payouts — largest single piece of new architecture (introduces a vendor identity type and ownership model across Catalog/Inventory/Orders).
- **Native mobile applications** (Android/iOS), consuming the same versioned REST API (API-first principle from SRS Part 1 §15 pays off here).
- **AI-powered recommendations / semantic search**, replacing/augmenting the Postgres full-text search from Phase 3.
- **Regional (South Asia) expansion**: multi-currency, cross-border shipping, additional languages — touches Orders/Payments/Shipping schemas (see ERD §8 open question on currency handling).
- **Tournament packages, equipment rental, membership programs** per the PVD Phase 4 vision.

---

## 7. Cross-Cutting Practices (apply from Phase 0 onward)

- **Traceability:** every PR references the User Story ID (`US-XXX-###`) it implements, per the backlog's traceability structure. This keeps Vision → BRD → SRS → Epic → Story → Code → Test traceable without extra tooling.
- **Testing:** unit tests per module, integration tests for cross-module flows (especially the Phase 5 checkout transaction), contract tests against the OpenAPI schema so the API Specification document and the implementation cannot silently drift.
- **Definition of Done:** unchanged from Product Backlog §12 — implemented, peer-reviewed, unit+integration tested, acceptance criteria met, no open critical/high defects, docs updated, deployed to the appropriate environment.
- **Module boundaries:** even though this is one deployable (modular monolith), each domain module keeps its own models/services/routes and communicates with others through explicit interfaces (service calls, not reaching into another module's DB tables directly) — this is what makes the SRS's "extract to microservices later without a rewrite" claim actually true when V3 arrives.
- **Feature flags** for anything shipped ahead of its dependencies being fully ready (e.g., a UI element for a V2 feature merged early) rather than long-lived branches.

---

## 8. Summary Timeline (MVP)

Indicative only — assumes one focused team running continuously; adjust for actual headcount and parallelization (Phases 2/3 and parts of 5/6 can overlap with enough engineers).

| Phase | Focus | Sprints |
| --- | --- | --- |
| 0 | Engineering foundations | 1 |
| 1 | Auth & Customers | 3 |
| 2 | Catalog & Inventory | 4 |
| 3 | Search & Discovery | 2 |
| 4 | Shopping Cart | 2 |
| 5 | Checkout, Payments & Orders | 5 |
| 6 | Shipping & Fulfillment | 2 |
| 7 | Notifications, Admin & Reporting | 4 |
| 8 | Hardening & Launch Readiness | 3 |
| **Total to MVP launch** | | **~26 sprints (~1 year at 2-week sprints, single team)** |

This is intentionally conservative for a from-scratch build of a transactional commerce platform with real payment integrations; a larger team running Phases 2+3, and 5+6, in parallel tracks could compress this materially.

---

## 9. Immediate Next Steps

1. Confirm team size/composition against the timeline in §8 and adjust phase durations accordingly.
2. Stand up Phase 0 (repo scaffolding, CI/CD, local dev environment) — this unblocks everything else and has no dependencies.
3. Resolve the two open schema questions flagged in the ERD document (§8: address snapshot strategy, currency handling) before Phase 5, since they affect the `orders`/`payments` schema directly.
4. Secure SSLCommerz and at least one courier provider's sandbox/API credentials early — these are the two external dependencies most likely to introduce lead time (merchant onboarding, KYC), and they gate Phase 5 and Phase 6 respectively.

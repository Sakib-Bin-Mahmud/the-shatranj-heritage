# UAT Checklist

Phase 8 (Hardening & MVP Launch Readiness) deliverable, mapped 1:1 to
the [Product Backlog & User Stories.md §14 "MVP Feature Summary"](Product%20Backlog%20and%20User%20Stories.md).

**Why this exists instead of a completed UAT sign-off:** UAT is
explicitly a human activity — real business stakeholders exercising
the product and deciding it's ready — and can't be executed
autonomously. What follows is the concrete, checkable test plan a
stakeholder (or whoever plays that role before one is available) runs
against a staging deployment; each item names the exact endpoint or
page to exercise and what "pass" looks like, so running it doesn't
require reverse-engineering the API first.

**Current coverage note:** every backend capability below (Phases 1–7)
is real and live at `/api/v1/...`, browsable via the auto-generated
docs at `/docs` on a running API instance. The customer-facing
storefront UI only covers auth/profile/addresses (Phase 1's Next.js
pages) — product browsing, cart, and checkout have no UI yet, only
APIs. Items under "Commerce" and "Customer Experience" that need those
pages are marked **(API only)** and should be tested via `/docs` or a
REST client until that UI exists; this is a known gap, not an oversight
— see the main README's Phase 7 note on the Admin Portal UI for the
equivalent gap on the admin side.

## Customer Experience

- [ ] **Registration & Login** — register with email (`/register`
      page or `POST /auth/register`) and with a Bangladeshi mobile
      number; log in with either identifier (`/login`); log out and
      confirm the session actually ends (`/auth/logout` revokes the
      refresh token — a reused old refresh token must fail).
- [ ] **Guest Checkout (API only)** — `POST /orders` with no bearer
      token and a `guest_email`/`guest_phone`, no prior registration
      required.
- [ ] **Product Browsing (API only)** — `GET /products` (pagination,
      category/price/material filters), `GET /categories`.
- [ ] **Product Search (API only)** — `GET /products?q=...`; confirm
      relevance ranking and that a no-results query returns category/
      featured-product suggestions instead of an empty page.
- [ ] **Product Details (API only)** — `GET /products/{slug}` returns
      variants, stock status, and images; `GET /products/{id}/related`.
- [ ] **Shopping Cart (API only)** — `POST /cart/items`, update
      quantity, remove an item, and confirm a guest cart merges into
      the customer's own cart on login/registration.
- [ ] **Checkout (API only)** — `POST /checkout/quote` then
      `POST /orders`; confirm the `Idempotency-Key` header actually
      prevents a duplicate order on a retried request.
- [ ] **Order Tracking (API only)** — `GET /orders/{order_number}` and
      `GET /orders/{order_number}/shipment` after an order has been
      shipped by an admin.
- [ ] **Customer Profile** — `/account` page: view profile, edit full
      name and preferred language (confirm the site's own English/
      Bangla toggle in the nav bar actually switches the UI), add/edit/
      delete a delivery address.

## Commerce

- [ ] **Product Catalog / Categories (API only, admin)** — as
      `content_manager`/`inventory_manager`: create a category, create
      a product with variants and images, confirm it appears in the
      public catalog once `status=active`.
- [ ] **Inventory (API only, admin)** — restock a variant, confirm
      `GET /admin/inventory` reflects it and a low-stock variant is
      flagged; confirm placing an order actually reserves stock
      (`quantity_reserved` increases) and cancelling an order releases
      it.
- [ ] **Payments (API only)** — place an order with an online payment
      method against the SSLCommerz sandbox, complete the sandbox
      payment flow, confirm the order moves to `confirmed` once the
      webhook lands; place a COD order and confirm no online payment
      step is required.
- [ ] **Shipping (API only, admin)** — as `order_manager`: assign a
      courier to a packed order, progress it through
      dispatched → in_transit → delivered, confirm the shipping cost
      shown at checkout matches the configured rate for the delivery
      district.
- [ ] **Order Management (API only, admin)** — list orders, filter by
      status, view an order's detail (items, payments, shipment), issue
      a refund request against a paid order.

## Administration

- [ ] **Product Management** — `POST/PATCH/DELETE` under
      `/admin/products` and `/admin/products/{id}/variants`; confirm
      RBAC — an account without `products.write` gets `403`.
- [ ] **Inventory Management** — `PATCH /admin/inventory/{variant_id}/adjust`
      for each `change_type` (restock/damage/adjustment) and confirm
      the resulting transaction ledger entry.
- [ ] **Customer Management** — `GET /admin/customers`, suspend/
      reactivate a customer via `PATCH /admin/customers/{id}/status`.
- [ ] **Order Management** — covered above under Commerce.
- [ ] **Reports** — `GET /admin/reports/sales`, `/revenue`,
      `/inventory`, `/customers`, `/products/top-selling`, `/refunds`;
      confirm the numbers match what was actually placed/adjusted
      during this UAT pass (they're live queries, not canned data).
- [ ] **User Management** — `POST /admin/users` to create a staff
      account with a role, `PATCH /admin/users/{id}/roles` to reassign
      it, confirm the new account can log in and only has access
      matching its role; `GET /admin/roles` lists all six roles with
      their permissions.

## Platform

- [ ] **Notifications** — trigger each of registration, password
      reset, order confirmation, payment confirmation, shipment
      dispatch, and delivery; confirm a corresponding row lands in the
      `notifications_log` table (no customer-visible UI for this one —
      it's a backend delivery guarantee, verified via the ledger).
- [ ] **Security** — confirm rate limiting kicks in on repeated login/
      register/forgot-password/reset-password/order-placement attempts
      (`429 RATE_LIMITED`); confirm the API refuses to boot with
      `ENVIRONMENT=production` and a placeholder secret still in
      `jwt_secret_key`/`payment_webhook_secret`/etc.
- [ ] **Audit Logging** — `GET /admin/audit-logs`; confirm a staff
      role reassignment, a customer status change, and a shipping-rate
      update each produce an entry with the correct before/after values.
- [ ] **Monitoring** — `GET /metrics` returns Prometheus text format;
      confirm `orders_placed_total` and `payment_webhook_results_total`
      increment after the Commerce-section tests above.
- [ ] **CMS (Basic)** — `GET /content/pages` lists the five seeded
      policy pages (Terms, Privacy, Return, Shipping, Warranty);
      `GET /content/pages/{slug}` renders one; as `content_manager`,
      publish/unpublish a page via `/admin/content/pages/{id}` and
      confirm it disappears from the public listing when unpublished.

## Sign-off

- [ ] No unresolved critical/high-severity defects found during this
      pass.
- [ ] Performance targets from SRS Part 4 hold under a basic load
      check (public reads <500ms, checkout <2s) — see
      `Deployment Runbook.md`'s promotion gate.
- [ ] Stakeholder(s) who ran this checklist: ______________________
- [ ] Date: ______________________
- [ ] Decision: ☐ Approved for production ☐ Blocked (list blockers above)

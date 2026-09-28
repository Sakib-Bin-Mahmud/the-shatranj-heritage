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
docs at `/docs` on a running API instance. As of Frontend Phase F9, the
customer-facing storefront (Next.js `F1`–`F4`) and the Admin Portal
(`F5`–`F8`) both have complete UIs covering every item below — nothing
in this checklist still requires exercising the API directly through
`/docs` or a REST client. A handful of Platform-section items
(Notifications, rate-limiting internals, Prometheus metrics) are
backend delivery guarantees with no customer- or admin-visible surface
by design; those are still marked **(API/ledger only)** and verified
against the database or `/metrics` directly, matching the original
Phase 8 design intent — see `Frontend Implementation Plan.md`'s F9
scope for the accessibility/localization/responsive/performance bar
the UI itself was held to.

## Customer Experience

- [ ] **Registration & Login** — register with email (`/register`
      page or `POST /auth/register`) and with a Bangladeshi mobile
      number; log in with either identifier (`/login`); log out and
      confirm the session actually ends (`/auth/logout` revokes the
      refresh token — a reused old refresh token must fail).
- [ ] **Guest Checkout** — as a signed-out visitor, add a product to
      the cart (`/cart`) and complete `/checkout` end to end (address →
      shipping → payment → review → place order) supplying only a
      guest email/phone, no account required; confirm the confirmation
      page (`/checkout/confirmation`) shows the order number and total.
- [ ] **Product Browsing** — `/products` (pagination, category/price/
      material/availability filters, sort), `/categories/{slug}`
      category detail pages.
- [ ] **Product Search** — the search box in the storefront nav bar;
      confirm relevance ranking and that a no-results query surfaces
      category/featured-product suggestions instead of an empty page.
- [ ] **Product Details** — `/products/{slug}`: variant selector,
      live stock status badge, image gallery, related products.
- [ ] **Shopping Cart** — `/cart`: update an item's quantity, remove
      an item, and confirm a guest cart merges into the customer's own
      cart after logging in or registering mid-session.
- [ ] **Checkout** — `/checkout`'s four-step flow (address, shipping,
      payment, review); confirm a duplicate submission of the same
      order (e.g. double-clicking "Place order" or retrying after a
      network blip) does not create two orders — the page's own
      idempotency key covers this, not something the tester supplies.
- [ ] **Order Tracking** — `/account/orders/{orderNumber}`: order
      status, payment status, and shipment tracking after an order has
      been shipped by an admin. A guest's only order-status view is the
      confirmation page shown immediately after placing the order
      (`/checkout/confirmation?order=...`), which looks itself up using
      the contact info just entered — there is no separate guest order
      lookup page or emailed link yet; note this as a known gap if a
      stakeholder expects one.
- [ ] **Customer Profile** — `/account` page: view profile, edit full
      name and preferred language (confirm the site's own English/
      Bangla toggle in the nav bar actually switches the UI), add/edit/
      delete a delivery address.

## Commerce

- [ ] **Product Catalog / Categories (admin)** — `/admin/content`
      (category tree) and `/admin/products` (`New product`, variant
      manager, image manager): as `content_manager`/`inventory_manager`,
      create a category, create a product with variants and images,
      confirm it appears in the public catalog once its status is
      "Active".
- [ ] **Inventory (admin)** — `/admin/inventory`: restock a variant via
      the adjustment form, confirm the list reflects it and a low-stock
      variant is flagged; confirm placing an order through `/checkout`
      actually reserves stock (available quantity drops) and cancelling
      the order from `/admin/orders/{orderId}` releases it.
- [ ] **Payments** — place an order through `/checkout` with an online
      payment method (bKash/Nagad/Rocket/card), complete the redirected
      SSLCommerz sandbox flow, confirm `/checkout/confirmation` and the
      admin order detail's Payments section both show it moved to
      "Confirmed" once the webhook lands; place a COD order through the
      same flow and confirm no online payment step is required.
- [ ] **Shipping (admin)** — `/admin/orders/{orderId}`'s Shipment
      section: as `order_manager`, assign a courier to a packed order,
      progress it through dispatched → in_transit → delivered; confirm
      the shipping cost shown at `/checkout`'s shipping step matches the
      configured rate for the delivery district (`/admin/settings`).
- [ ] **Order Management (admin)** — `/admin/orders`: list, filter by
      status, view an order's detail (items, payments, shipment), issue
      a refund request against a paid order via the Refund section.

## Administration

- [ ] **Product Management** — `/admin/products`: create, edit, and
      archive a product and its variants/images; confirm the sidebar
      itself hides "Products" for an account without `products.write`,
      and separately confirm the API still refuses the equivalent
      request with `403` if called directly (the UI hiding a link is
      not the security boundary — the permission check is).
- [ ] **Inventory Management** — `/admin/inventory`'s adjustment form,
      exercised for each change type (restock/damage/adjustment); confirm
      the resulting entry in `/admin/audit-logs`.
- [ ] **Customer Management** — `/admin/customers`: search/list, view a
      customer's detail, suspend and reactivate their account.
- [ ] **Order Management** — covered above under Commerce.
- [ ] **Reports** — `/admin/reports`'s Sales, Revenue, Customers,
      Inventory, Top Products, and Refunds tabs (plus the summary cards
      on `/admin`'s dashboard); confirm the numbers match what was
      actually placed/adjusted during this UAT pass (they're live
      queries, not canned data).
- [ ] **User Management** — `/admin/staff`: create a staff account with
      a role, reassign its role, confirm the new account can log in
      and only sees the sidebar sections matching its role; the
      Permissions Reference panel lists all six roles with their
      permissions. Confirm a super admin cannot demote their own
      account to a role without `staff.manage` (self-lockout guard).

## Platform

- [ ] **Notifications (ledger only)** — trigger each of registration,
      password reset, order confirmation, payment confirmation,
      shipment dispatch, and delivery through their respective pages;
      confirm a corresponding row lands in the `notifications_log`
      table (there is no customer-visible notification center by
      design — it's a backend delivery guarantee, verified via the
      ledger, not a page).
- [ ] **Security (API/ledger only)** — confirm rate limiting kicks in
      on repeated login/register/forgot-password/reset-password/
      order-placement attempts from their respective pages (`429
      RATE_LIMITED` — the same guard `/admin/login` hit during this
      phase's own E2E test runs); confirm the API refuses to boot with
      `ENVIRONMENT=production` and a placeholder secret still in
      `jwt_secret_key`/`payment_webhook_secret`/etc.
- [ ] **Audit Logging** — `/admin/audit-logs`: filter by action/actor;
      confirm a staff role reassignment (`/admin/staff`), a customer
      status change (`/admin/customers/{id}`), and a shipping-rate
      update (`/admin/settings`) each produce an entry with the correct
      before/after values.
- [ ] **Monitoring (API only)** — `GET /metrics` returns Prometheus
      text format; confirm `orders_placed_total` and
      `payment_webhook_results_total` increment after the
      Commerce-section tests above (no admin UI surfaces these by
      design — they feed an external monitoring stack, per the
      Deployment Runbook).
- [ ] **CMS (Basic)** — `/legal` lists the five seeded policy pages
      (Terms, Privacy, Return, Shipping, Warranty); `/legal/{slug}`
      renders one; as `content_manager`, publish/unpublish a page from
      `/admin/content`'s Content tab and confirm it disappears from the
      public `/legal` listing when unpublished.

## Sign-off

- [ ] No unresolved critical/high-severity defects found during this
      pass.
- [ ] Performance targets from SRS Part 4 hold under a basic load
      check (public reads <500ms, product detail <3s, search <1s,
      checkout <2s) — see `Deployment Runbook.md`'s promotion gate.
- [ ] Storefront pages are usable at phone width and the Admin Portal
      at tablet width (NFR-USA-003); a screen-reader pass over the
      golden paths (guest checkout, order tracking, admin order
      fulfillment) finds no unlabeled controls or unannounced errors.
- [ ] Stakeholder(s) who ran this checklist: ______________________
- [ ] Date: ______________________
- [ ] Decision: ☐ Approved for production ☐ Blocked (list blockers above)

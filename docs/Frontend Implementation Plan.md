# Frontend Implementation Plan

**Project Name:** The Shatranj Heritage
**Document Version:** 1.0 (Draft)
**Document Owner:** Engineering
**Status:** Draft
**Last Updated:** September 2026

---

## 1. Purpose

The backend (`apps/api`) is complete through Phase 8 of [Implementation Plan.md](Implementation%20Plan.md) — every module in the API Specification has real, tested endpoints, and Phase 8 hardened them for production traffic. The frontend (`apps/web`), by contrast, only covers Phase 1's slice: registration, login, profile, and address management. Product browsing, cart, checkout, order tracking, and the entire Admin Portal exist as backend APIs with no UI.

This document sequences the remaining frontend work the same way the backend plan sequenced the API: phases with a stated objective, scope pinned to real endpoints that already exist, and exit criteria — not a wishlist.

## 2. Guiding Constraints

Decisions this plan makes so later phases don't re-litigate them:

| Area | Decision | Rationale |
| --- | --- | --- |
| Styling | Keep CSS Modules (no Tailwind/CSS-in-JS) | Matches the existing Phase 1 pages (`form.module.css`, `nav-bar.module.css`); introducing a second styling system mid-project means rewriting what's already shipped for no functional gain. |
| Server state | Add [TanStack Query](https://tanstack.com/query) | The existing hand-rolled `useEffect` + `useState` fetch pattern (`account/page.tsx`) doesn't scale to the ~15 list/detail/mutation screens the Admin Portal alone needs. This is the one new runtime dependency this plan adds to `apps/web`. |
| Charts | Add [Recharts](https://recharts.org) for Phase F8 only | Lightweight, composable, and easiest to keep accessible/non-generic per the dataviz skill's guidance — not needed before the reporting phase, so it's deferred rather than installed up front. |
| API client | Extend `src/lib/api-client.ts`, not replace it | It already handles auth headers, error envelopes, and `ApiClientError`; each phase adds typed request/response helpers for its own module rather than a rewrite. |
| Design language | Two token sets, not one | **Themed** (Enchanted Chess Hall — obsidian/parchment/gold/emerald, Cinzel/EB Garamond) for the homepage and marketing surfaces only; **Functional** (today's clean black/white/gray) for catalog, cart, checkout, account, and the entire Admin Portal. This is the scope boundary agreed when the theme was designed — see the [theme concept canvas](https://claude.ai/artifact/SMuAVhoF6vj1dYwtpskoab). |
| Admin visual identity | Deliberately plain, desktop-first | Staff tools optimize for density and speed, not brand mood — distinct from the customer storefront on purpose. |
| i18n | English/Bangla for the customer storefront; English-only for the Admin Portal (recommended) | NFR-LOC-001 targets customers, not staff; most back-office tools ship in one operating language. Flagged as a decision to confirm, not assumed silently. |
| Testing | Playwright E2E for golden paths, added in the final phase | The backend's own test suite (129 tests) can't catch a frontend regression; a handful of end-to-end flows catch the ones that matter without the maintenance cost of testing every screen this way. |

## 3. Phase Sequence

| Phase | Title | Depends On |
| --- | --- | --- |
| F0 | Foundations: Design System & Tooling | — |
| F1 | Homepage & Marketing (Enchanted Chess Hall theme) | F0 |
| F2 | Product Catalog, Search & Discovery | F0 |
| F3 | Cart & Checkout | F2 |
| F4 | Order Tracking & Account Expansion | F3 |
| F5 | Admin Portal: Shell, Auth & Dashboard | F0 |
| F6 | Admin Portal: Catalog, Inventory & Content | F5 |
| F7 | Admin Portal: Orders, Shipping, Customers & Staff | F5 |
| F8 | Admin Portal: Reporting & Analytics | F5 |
| F9 | Cross-Cutting Hardening & Launch QA | F1–F8 |

F1–F4 (storefront) and F5–F8 (admin) are independent after F0 and can run in either order, or in parallel across two workstreams, since they share almost no components beyond the design-system primitives F0 builds.

---

### Phase F0 — Foundations: Design System & Tooling (~1–2 sprints)

**Objective:** Everything later phases build on, built once, so no phase after this one reworks tooling or restyles a screen it already shipped.

**Scope:**
- Add TanStack Query; wrap the app root in its provider alongside the existing `AuthProvider`/`DictionaryProvider`.
- Formalize both token sets as CSS custom properties: `theme.css` (Enchanted Chess Hall — obsidian/charcoal/parchment/gold/emerald/oxblood, Cinzel/Cinzel Decorative/EB Garamond) scoped to marketing routes only, and `tokens.css` (today's functional palette, extended with a few semantic tokens — success/warning/danger, surface levels — the admin tables and forms will need).
- Four layout shells: **Marketing** (themed nav/footer, for F1), **Storefront** (functional nav with cart icon + item count, for F2–F4), **Account** (today's layout, extended), **Admin** (sidebar nav, RBAC-aware, for F5–F8).
- Shared component primitives, built once and themed by whichever token set their layout applies: Button, Input/Select/Checkbox (extending the existing `<label><input></label>` pattern), Card, Badge, Table (sortable/paginated), Pagination, inline Alert (reusing the `role="alert"`/`role="status"` pattern from Phase 8), Modal/Dialog, EmptyState, Skeleton loading state.
- Typed API client helpers per backend module (catalog, cart, checkout, orders, payments, admin, reports), generated by hand from the OpenAPI schema CI already exports (`apps/api`'s `ci.yml` uploads `openapi.json` as an artifact — pull the current shape from there rather than re-deriving it from route code).

**Exit criteria:** `npm run typecheck && npm run lint && npm run build` all green with zero pages yet built on top; both non-marketing layout shells render with the primitive components in a throwaway `/internal/design-preview` route (deleted before F9's launch QA, or kept behind an admin-only guard).

---

### Phase F1 — Homepage & Marketing Surfaces (~1–2 sprints)

**Objective:** Ship the themed top-of-funnel — the [reviewed design concept](https://claude.ai/artifact/SMuAVhoF6vj1dYwtpskoab) becomes real code.

**Scope:**
- Homepage: hero, "The Grand Collection" (real featured products via `GET /products?featured=true`, not static content), "Masters of the Craft" (static copy for now — see gap below), "The Maker's Oath" trust strip (static), "Join the Circle" newsletter section.
- **Known gap to resolve in this phase:** no backend endpoint captures a newsletter signup today. Options: (a) add a minimal `POST /newsletter/subscribe` endpoint + table as a small backend addition riding along with this phase, or (b) ship the section as visually complete but non-functional and mark it explicitly TODO. Decide before building the form; don't wire it to nothing silently.
- Legal/policy pages (`GET /content/pages`, `GET /content/pages/{slug}`) rendered in the **functional** token set, not the theme — a Terms & Conditions page should stay maximally readable, not candle-lit.
- Homepage metadata/OpenGraph tags.

**Exit criteria:** homepage visually matches the reviewed canvas; all five seeded policy pages render live CMS content; Lighthouse accessibility score and the Phase 8 a11y bar (live regions, contrast, keyboard nav) both hold on every new page.

---

### Phase F2 — Product Catalog, Search & Discovery (~2 sprints)

**Objective:** Let customers actually find products — the core commerce surface everything downstream depends on.

**Scope:**
- Category pages: tree navigation (`GET /categories`), category detail listing (`GET /categories/{slug}`).
- Product listing/grid: `GET /products` with every filter as a real control — search (`q`), category, price range, material, availability, featured, sort — plus pagination and the API's own no-results suggestions (don't reimplement that logic client-side).
- Product detail page: `GET /products/{slug}` — variant selector driven by real `attributes`, image gallery, live stock/availability badge, related products (`GET /products/{id}/related`), add-to-cart.
- Search input in the storefront nav, wired to the listing page's `q` param.

**Exit criteria:** browse → filter/search → product detail is a dead-end-free journey against the real API; a search with zero results shows the category/featured-product suggestions the backend already computes.

---

### Phase F3 — Cart & Checkout (~2–3 sprints)

**Objective:** Convert browsing into a placed order — the highest-stakes flow in the app, and the one Phase 5–6 of the backend plan was built entirely to support.

**Scope:**
- Cart (drawer or page): guest (cookie-based) and customer (token-based), relying on the backend's own guest→customer merge-on-login — the frontend just needs to call the existing endpoints in the right order, not reimplement the merge.
- Checkout, as a multi-step flow: address (select a saved one, add a new one, or guest inline address + contact), shipping method with a live quote (`POST /checkout/quote`, showing the real district/weight-based cost — never a client-computed estimate), payment method (bKash/Nagad/Rocket/card via SSLCommerz redirect, or COD), review, place order.
- A client-generated `Idempotency-Key`, persisted (e.g. in the checkout form's local state or `sessionStorage`) across a retry of the same attempt — this is what makes the backend's replay protection actually reachable from the UI.
- Post-checkout: the SSLCommerz redirect return (success/fail/cancel query params), an order confirmation page, and an explicit "payment confirming" state for the window between redirect-back and the webhook actually landing (the order isn't `confirmed` yet at that instant — don't show a false success).

**Exit criteria:** a full guest checkout and a full logged-in checkout both complete end-to-end against the SSLCommerz sandbox and COD; double-submitting the place-order button (or retrying after a network blip) never creates two orders.

---

### Phase F4 — Order Tracking & Account Expansion (~1 sprint)

**Objective:** Close the loop after purchase and round out the account area Phase 1 started.

**Scope:**
- Order history list + detail as a new tab in `/account` (`GET /orders`, `GET /orders/{order_number}`).
- Shipment tracking display (`GET /orders/{order_number}/shipment`).
- Order cancellation (`POST /orders/{order_number}/cancel`) — surface BR-ORD-003's real eligibility rule as a disabled state with an explanation, not a button that fails after the click.
- Payment retry for a failed/abandoned online payment (`POST /payments/initiate`).

**Exit criteria:** a customer can find any past order, see live tracking, cancel when eligible, and retry a failed payment, all without leaving `/account`.

---

### Phase F5 — Admin Portal: Shell, Auth & Dashboard (~1–2 sprints)

**Objective:** Stand up the operational surface Phase 7 of the backend plan built APIs for and explicitly deferred the UI on.

**Scope:**
- Admin route group (e.g. `/admin/*`) with its own login (`POST /admin/auth/login`), its own layout (sidebar, the functional token set, nothing themed), and navigation gated by the permission codes embedded in the admin access token — a role sees only the sections its permissions cover.
- Dashboard landing page summarizing `GET /admin/reports/sales` and `GET /admin/reports/inventory`.
- Admin session handling: refresh flow, logout.

**Exit criteria:** each of the six roles (`super_admin`, `inventory_manager`, `content_manager`, `marketing_manager`, `order_manager`, `customer_support`) logs in and sees exactly the sections its permissions allow — verified against all six, not just `super_admin`.

---

### Phase F6 — Admin Portal: Catalog, Inventory & Content (~2 sprints)

**Objective:** Let staff run the catalog without touching the database — Phase 7's own exit criterion, finally given a UI.

**Scope:**
- Category management: tree view, create/edit/deactivate.
- Artisan management: create/edit.
- Product management: filterable list, create/edit form with variants and multi-image upload, archive.
- Inventory: stock list with a low-stock filter, an adjustment form (restock/damage/adjustment) that shows the resulting transaction ledger entry per variant.
- CMS: policy page list, create/edit with a publish/unpublish toggle.

**Exit criteria:** a `content_manager`/`inventory_manager` account can take a product from nonexistent to live-with-stock-and-images entirely through the UI.

---

### Phase F7 — Admin Portal: Orders, Shipping, Customers & Staff (~2 sprints)

**Objective:** The rest of day-to-day store operations.

**Scope:**
- Orders: filterable list, detail view (items, payments, shipment), status transitions, refund issuance.
- Shipping: courier assignment (manual tracking number or provider-booked), status progression through delivery.
- Customers: list/search, detail, suspend/reactivate.
- Staff & roles: staff list, create-staff-with-role(s) form, role reassignment, a read-only roles/permissions reference.
- Settings: shipping-rate table, viewable and editable.
- Audit log: filterable viewer over every recorded admin/system action.

**Exit criteria:** an `order_manager` account can run an order from placed to delivered without the database; a `super_admin` can onboard a new staff member end-to-end through the UI.

---

### Phase F8 — Admin Portal: Reporting & Analytics (~1–2 sprints)

**Objective:** Turn the six reporting endpoints into an actual decision-support surface instead of raw JSON.

**Scope:**
- Sales dashboard (totals, orders-by-status).
- Revenue-over-time chart (day/week/month) — the app's first real chart; use Recharts (per §2) and the dataviz skill's guidance on accessible, non-generic chart styling.
- Inventory health (low-stock + slow-moving lists).
- Customer growth chart + repeat-customer rate.
- Top-selling products table.
- Refund analysis (by-status breakdown).

**Exit criteria:** every number on every report screen matches the API's own response for the same date range — no client-side recomputation that could silently drift from the backend's math.

---

### Phase F9 — Cross-Cutting Hardening & Launch QA (~2 sprints)

**Objective:** The frontend's equivalent of the backend's own Phase 8 — the NFRs that cut across everything F1–F8 built, done once at the end rather than piecemeal.

**Scope:**
- Accessibility: extend the Phase 8 pattern (`role="alert"`/`role="status"` live regions, `autoComplete`, dynamic `<html lang>`, keyboard navigation, focus management) to every page built in F1–F8, not just the original auth/account pages it was proven on.
- Localization: extend the English/Bangla dictionary to catalog, cart, checkout, and order tracking. Confirm the §2 recommendation (Admin Portal stays English-only) before treating it as decided.
- Responsive/mobile QA (NFR-USA-003) across the full customer journey (F1–F4) — phone-first. The Admin Portal (F5–F8) is desktop-first by design; verify it's usable on a tablet, not a phone.
- Performance: `next/image` for product photography, route-level code splitting, and re-verifying the NFR-PER-001..004 targets now that real pages exist to measure against (public reads <500ms, product detail <3s, checkout <2s, search <1s).
- Playwright end-to-end coverage for the golden paths: guest checkout, logged-in checkout, admin product creation, admin order fulfillment — the regressions the backend's 129-test suite structurally cannot see.
- Re-run [UAT Checklist.md](UAT%20Checklist.md) against the now-complete frontend, replacing every "(API only)" line item with the real page it now has.

**Exit criteria:** this is the MVP frontend launch gate — the same bar Phase 8 set for the backend, now met by the UI in front of it.

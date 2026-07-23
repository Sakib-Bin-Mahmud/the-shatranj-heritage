# API Specification

**Project Name:** The Shatranj Heritage
**Document Version:** 1.0 (Draft)
**Style:** REST over HTTPS, JSON
**Status:** Draft
**Last Updated:** July 2026

---

## 1. Purpose

This document is the implementation-ready API contract for The Shatranj Heritage backend. It builds on the conventions sketched in the [Software Requirements Specification](Software%20Requirements%20Specification.md) (Part 3) and the tables in the [ERD & Database Schema](Entity%20Relationship%20Diagram%20and%20Database%20Schema.md), and is what backend route handlers and frontend API clients should both be built against.

Every endpoint below traces back to a functional requirement (`FR-...`) or user story (`US-...`) from the SRS / Product Backlog. Endpoints for V2-scope features (wishlist, reviews, coupons admin, CMS) are included now so the contract doesn't need reshaping later, but can be implemented after the MVP set. Vendor/Marketplace (V3) endpoints are excluded, matching the ERD's scope decision.

---

## 2. Conventions

### Base URL & Versioning

```
/api/v1
```

Breaking changes get a new version prefix (`/api/v2`); additive changes (new optional fields, new endpoints) do not.

### Authentication

`Authorization: Bearer <access_token>` (JWT). Access tokens are short-lived (~15 min); `POST /auth/refresh` exchanges a valid refresh token for a new access token. Endpoints are marked with one of:

| Marker | Meaning |
| --- | --- |
| **Public** | No auth required |
| **Customer** | Requires a valid customer access token |
| **Admin** | Requires a valid admin access token; specific role noted where narrower than "any staff role" |

Admin endpoints all live under `/admin/...` so the RBAC boundary is visible in the URL, not just enforced in code.

### Standard Response Envelope

Success:
```json
{ "success": true, "data": { }, "message": "Request completed successfully." }
```

Error:
```json
{ "success": false, "error": { "code": "PRODUCT_NOT_FOUND", "message": "Requested product does not exist." } }
```

### Pagination

List endpoints accept `page` (default `1`) and `limit` (default `20`, max `100`) query params. Responses include:
```json
"meta": { "page": 1, "limit": 20, "total": 134, "total_pages": 7 }
```

### Sorting & Filtering

Module-specific query params are documented per endpoint. Sorting uses a single `sort` param with named values (e.g. `sort=price_asc`, `sort=newest`) rather than separate `sort_by`/`sort_dir` params, to keep the allowed set explicit and validated.

### Idempotency

`POST /orders` and `POST /payments/initiate` require an `Idempotency-Key` header (client-generated UUID). A retried request with the same key returns the original result instead of creating a duplicate — this is what backs NFR-REL-001 (each order created exactly once) at the API layer.

### Rate Limiting

`POST /auth/login`, `POST /auth/register`, `POST /auth/forgot-password`, and OTP endpoints are rate-limited per client/IP (NFR-SEC-006). Exceeding the limit returns `429` with error code `RATE_LIMITED`.

### Common Error Codes

| HTTP | Code | Meaning |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | Malformed request |
| 401 | `UNAUTHENTICATED` | Missing/invalid/expired token |
| 403 | `FORBIDDEN` | Authenticated but not authorized for this action |
| 404 | `NOT_FOUND` | Resource doesn't exist |
| 409 | `CONFLICT` | Duplicate resource (e.g. email already registered) |
| 422 | `UNPROCESSABLE_ENTITY` | Valid request shape, but violates a business rule (e.g. insufficient stock) |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

Endpoint-specific error codes are noted inline where they add information beyond this table.

---

## 3. Endpoint Inventory

Quick reference for every endpoint. Full request/response detail for non-trivial endpoints follows in Section 4.

### 3.1 Auth

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `POST /auth/register` | Public | Register with email or mobile | US-AUTH-001/002 |
| `POST /auth/login` | Public | Login with email/mobile + password | US-AUTH-003 |
| `POST /auth/logout` | Customer | Invalidate current session | US-AUTH-007 |
| `POST /auth/refresh` | Public (refresh token) | Exchange refresh token for new access token | FR-AUTH-002 |
| `POST /auth/forgot-password` | Public | Request password reset link/OTP | US-AUTH-005 |
| `POST /auth/reset-password` | Public | Complete password reset | US-AUTH-006 |
| `POST /auth/verify-email` *(V2)* | Customer | Confirm email verification token | US-AUTH-008 |
| `POST /auth/mobile-otp/request` *(V2)* | Customer | Request mobile OTP | US-AUTH-009 |
| `POST /auth/mobile-otp/confirm` *(V2)* | Customer | Confirm mobile OTP | US-AUTH-009 |

### 3.2 Customers

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /customers/me` | Customer | Get own profile | US-CUS-001 |
| `PATCH /customers/me` | Customer | Update own profile | US-CUS-002 |
| `PATCH /customers/me/preferences` *(V2)* | Customer | Update communication preferences | US-CUS-006 |
| `DELETE /customers/me` *(V2)* | Customer | Request account deactivation | US-CUS-007 |
| `GET /customers/me/addresses` | Customer | List own addresses | US-CUS-003 |
| `POST /customers/me/addresses` | Customer | Add address | US-CUS-003 |
| `PATCH /customers/me/addresses/{id}` | Customer | Update address | US-CUS-003 |
| `DELETE /customers/me/addresses/{id}` | Customer | Remove address | US-CUS-003 |
| `GET /admin/customers` | Admin | List/search customers | FR-ADM-004 |
| `GET /admin/customers/{id}` | Admin | Customer detail | FR-ADM-004 |
| `PATCH /admin/customers/{id}/status` | Admin | Suspend/reactivate customer | FR-ADM-004 |

### 3.3 Catalog (Categories, Products, Variants, Images)

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /categories` | Public | List categories (tree) | US-CAT-003 |
| `GET /categories/{slug}` | Public | Category detail | US-CAT-003 |
| `GET /products` | Public | Search/filter/sort products | FR-SCH-001…007, US-SRC-001…003 |
| `GET /products/{slug}` | Public | Product detail | US-CAT-002 |
| `GET /products/{id}/related` | Public | Related products | US-CAT-006 |
| `POST /admin/categories` | Admin (Content) | Create category | FR-ADM-001 |
| `PATCH /admin/categories/{id}` | Admin (Content) | Update category | FR-ADM-001 |
| `DELETE /admin/categories/{id}` | Admin (Content) | Remove category | FR-ADM-001 |
| `POST /admin/products` | Admin (Inventory) | Create product | FR-CAT-001 |
| `PATCH /admin/products/{id}` | Admin (Inventory) | Update product | FR-CAT-002 |
| `DELETE /admin/products/{id}` | Admin (Inventory) | Archive product | FR-CAT-003 |
| `POST /admin/products/{id}/variants` | Admin (Inventory) | Add variant | FR-CAT-005 |
| `PATCH /admin/products/{id}/variants/{variantId}` | Admin (Inventory) | Update variant | FR-CAT-005 |
| `DELETE /admin/products/{id}/variants/{variantId}` | Admin (Inventory) | Remove variant | FR-CAT-005 |
| `POST /admin/products/{id}/images` | Admin (Inventory) | Upload product image | FR-CAT-004 |
| `DELETE /admin/products/{id}/images/{imageId}` | Admin (Inventory) | Remove image | FR-CAT-004 |
| `GET /search/suggestions` *(V2)* | Public | Autocomplete suggestions | US-SRC-004 |

### 3.4 Cart & Wishlist

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /cart` | Public/Customer | Get current cart (guest via session, customer via token) | US-CRT-004 |
| `POST /cart/items` | Public/Customer | Add item to cart | US-CRT-001 |
| `PATCH /cart/items/{itemId}` | Public/Customer | Update item quantity | US-CRT-002 |
| `DELETE /cart/items/{itemId}` | Public/Customer | Remove item | US-CRT-003 |
| `POST /cart/coupon` | Public/Customer | Apply coupon to cart | US-CHK-005 |
| `DELETE /cart/coupon` | Public/Customer | Remove applied coupon | US-CHK-005 |
| `GET /wishlist` *(V2)* | Customer | List wishlist items | US-WSH-002 |
| `POST /wishlist/items` *(V2)* | Customer | Add product to wishlist | US-WSH-001 |
| `DELETE /wishlist/items/{productId}` *(V2)* | Customer | Remove from wishlist | US-WSH-003 |
| `POST /wishlist/items/{productId}/move-to-cart` *(V2)* | Customer | Move item to cart | US-WSH-004 |

### 3.5 Checkout & Orders

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `POST /checkout/quote` | Public/Customer | Preview totals & shipping options for current cart + address | US-CHK-003, US-CHK-004 |
| `POST /orders` | Public/Customer | Place order (checkout) | US-CHK-006 |
| `GET /orders` | Customer | List own orders | US-CUS-004 |
| `GET /orders/{orderNumber}` | Customer | Order detail | US-ORD-004 |
| `POST /orders/{orderNumber}/cancel` | Customer | Cancel eligible order | US-ORD-003 |
| `GET /orders/{orderNumber}/shipment` | Customer | Shipment/tracking info | US-SHP-003 |
| `GET /admin/orders` | Admin (Order) | List/filter all orders | FR-ADM-003 |
| `GET /admin/orders/{id}` | Admin (Order) | Order detail | FR-ADM-003 |
| `PATCH /admin/orders/{id}/status` | Admin (Order) | Update order status | US-ORD-002/003 |
| `POST /admin/orders/{id}/shipment` | Admin (Order) | Assign courier + tracking number | US-SHP-002 |
| `PATCH /admin/shipments/{id}/status` | Admin (Order) | Update shipment status | US-SHP-004 |
| `POST /admin/orders/{id}/refund` | Admin (Order) | Initiate refund | US-PAY-005 |

### 3.6 Payments

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `POST /payments/initiate` | Public/Customer | Start payment for an order | US-PAY-001/002 |
| `POST /payments/webhook/sslcommerz` | Public (signature-verified) | Gateway payment callback | US-PAY-003/004 |
| `GET /payments/{id}/status` | Customer | Poll payment status | US-PAY-004 |
| `GET /admin/payments` | Admin (Order) | List/filter payments | FR-RPT-006 |

### 3.7 Reviews *(V2)*

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /products/{id}/reviews` | Public | List approved reviews for a product | US-CAT-002 |
| `POST /products/{id}/reviews` | Customer | Submit review (verified purchase only) | US-REV-002 |
| `GET /admin/reviews` | Admin (Content) | Moderation queue | FT-REV-003 |
| `PATCH /admin/reviews/{id}/status` | Admin (Content) | Approve/reject review | FT-REV-003 |

### 3.8 Inventory (Admin)

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /admin/inventory` | Admin (Inventory) | List stock levels, filter by low-stock | US-INV-002 |
| `PATCH /admin/inventory/{variantId}/adjust` | Admin (Inventory) | Adjust stock (restock/damage/correction) | US-INV-001 |
| `GET /admin/inventory/{variantId}/transactions` | Admin (Inventory) | Stock movement history | US-INV-003 |

### 3.9 Promotions

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `POST /coupons/validate` | Public/Customer | Validate a coupon code against current cart | US-CHK-005 |
| `GET /admin/coupons` | Admin (Marketing) | List coupons | US-PRM-001 |
| `POST /admin/coupons` | Admin (Marketing) | Create coupon | US-PRM-001 |
| `PATCH /admin/coupons/{id}` | Admin (Marketing) | Update coupon | US-PRM-001/002 |
| `DELETE /admin/coupons/{id}` | Admin (Marketing) | Deactivate coupon | US-PRM-001 |

### 3.10 Content (CMS) *(V2)*

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /content/pages/{slug}` | Public | Static/policy page | FR-CMS-004 |
| `GET /content/blog` | Public | List published posts | FR-CMS-002 |
| `GET /content/blog/{slug}` | Public | Blog post detail | FR-CMS-002 |
| `POST /admin/content/pages` | Admin (Content) | Create page | FR-CMS-004 |
| `PATCH /admin/content/pages/{id}` | Admin (Content) | Update page | FR-CMS-004 |
| `POST /admin/content/blog` | Admin (Content) | Create post | FR-CMS-002 |
| `PATCH /admin/content/blog/{id}` | Admin (Content) | Update/publish post | FR-CMS-002 |

### 3.11 Admin Users & RBAC

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /admin/users` | Admin (Super Admin) | List staff accounts | US-ADM-003 |
| `POST /admin/users` | Admin (Super Admin) | Create staff account | US-ADM-003 |
| `PATCH /admin/users/{id}/roles` | Admin (Super Admin) | Assign roles | US-ADM-004 |
| `GET /admin/roles` | Admin (Super Admin) | List roles & permissions | FR-ADM-007 |

### 3.12 Reporting (Admin)

| Method & Path | Auth | Summary | Maps to |
| --- | --- | --- | --- |
| `GET /admin/reports/sales` | Admin | Sales dashboard metrics | US-RPT-001 |
| `GET /admin/reports/revenue` | Admin | Revenue over time | FR-RPT-002 |
| `GET /admin/reports/inventory` | Admin | Slow-moving / low-stock report | US-RPT-002 |
| `GET /admin/reports/customers` | Admin | Customer growth/insights | US-RPT-003 |
| `GET /admin/reports/products/top-selling` | Admin | Best-selling products | FR-RPT-005 |
| `GET /admin/reports/refunds` | Admin | Refund analysis | FR-RPT-006 |

---

## 4. Detailed Endpoint Specs

Only endpoints with non-obvious request/response shapes or business rules are detailed here; the rest follow standard CRUD shapes against the fields defined in the ERD document.

### `POST /auth/register`
**Public** · Maps to US-AUTH-001, US-AUTH-002, FR-AUTH-001

Request body — one of `email` or `mobile_number` required:
```json
{ "email": "player@example.com", "mobile_number": null, "password": "•••••••", "full_name": "Karim Ahmed" }
```
Response `201`:
```json
{ "customer": { "id": "...", "email": "...", "full_name": "..." }, "access_token": "...", "refresh_token": "..." }
```
Errors: `409 EMAIL_ALREADY_EXISTS`, `409 MOBILE_ALREADY_EXISTS`, `400 VALIDATION_ERROR` (weak password / bad mobile format).

---

### `POST /auth/login`
**Public** · Maps to US-AUTH-003, FR-AUTH-002

Request: `{ "identifier": "player@example.com", "password": "•••••••" }` — `identifier` accepts email or mobile number.

Response `200`: same shape as register. Failed attempts are rate-limited (NFR-SEC-006); invalid credentials return a generic `401 INVALID_CREDENTIALS` regardless of whether the identifier exists, to avoid account enumeration.

---

### `GET /products`
**Public** · Maps to FR-SCH-001…007, US-SRC-001…003

Query params:

| Param | Type | Notes |
| --- | --- | --- |
| `q` | string | Keyword search (name, SKU, description) |
| `category` | slug | Filter by category |
| `price_min`, `price_max` | number | |
| `material` | string | Matches `product_variants.attributes.material` |
| `availability` | `in_stock` \| `all` | Default `all` |
| `sort` | `price_asc` \| `price_desc` \| `newest` \| `best_selling` \| `rating` \| `alphabetical` | Default `newest` |
| `page`, `limit` | int | Standard pagination |

Response `200`: paginated array of product summaries (`id`, `slug`, `name`, `primary_image_url`, `price`, `stock_status`).

---

### `POST /admin/products`
**Admin (Inventory Manager+)** · Maps to FR-CAT-001, BR-PRO-001

Request body mirrors the `products` table: `sku` (unique), `name`, `category_id`, `artisan_id?`, `description`, `base_price`, `weight_grams?`, `status` (defaults to `draft`). Variants are created separately via the variants sub-resource so a product can be published incrementally.

Errors: `409 SKU_ALREADY_EXISTS`, `422 CATEGORY_NOT_FOUND`.

---

### `POST /cart/items`
**Public/Customer** · Maps to US-CRT-001

Guest carts are identified by a `cart_session_id` cookie set on first interaction; authenticated requests resolve the cart via `customer_id` instead. On login, an active guest cart is merged into the customer's cart.

Request: `{ "product_variant_id": "...", "quantity": 1 }`

Response `200`: full updated cart (items, subtotal, item count). Errors: `422 INSUFFICIENT_STOCK` (validated against `inventory.quantity_on_hand - quantity_reserved`).

---

### `POST /checkout/quote`
**Public/Customer** · Maps to US-CHK-003, US-CHK-004

Request: `{ "address_id": "..." }` (or an inline address for guests) `, "shipping_method": "standard" | "express" }`

Response `200`: `{ "subtotal", "shipping_amount", "discount_amount", "tax_amount", "total_amount", "shipping_options": [...] }`. Stateless — does not reserve inventory or create any record; purely a pricing preview before `POST /orders`.

---

### `POST /orders`
**Public/Customer** · Requires `Idempotency-Key` header · Maps to US-CHK-006, FR-ORD-001, NFR-REL-001

Request: `{ "address_id" | inline address, "shipping_method", "payment_method", "coupon_code?" }`

Behavior: revalidates cart inventory, reserves stock (`inventory.quantity_reserved` incremented), creates the order + order_items with price/name/SKU snapshots, and — for non-COD methods — returns a payment redirect via the payments module. Cart is cleared on success.

Response `201`: `{ "order": { "order_number", "status", "total_amount", ... }, "payment": { "redirect_url" } | null }`

Errors: `422 INSUFFICIENT_STOCK`, `422 INVALID_COUPON`, `404 ADDRESS_NOT_FOUND`.

---

### `POST /payments/initiate`
**Public/Customer** · Requires `Idempotency-Key` header · Maps to US-PAY-001, FR-PAY-001

Request: `{ "order_id": "...", "method": "bkash" | "nagad" | "rocket" | "card" | "cod" }`

For online methods, creates a `pending` payment row and returns a gateway redirect URL from SSLCommerz. For `cod`, marks the order `awaiting_payment` immediately with no external call.

Response `200`: `{ "payment_id", "status", "redirect_url"? }`

---

### `POST /payments/webhook/sslcommerz`
**Public, signature-verified** · Maps to US-PAY-003, US-PAY-004

Not customer-authenticated — authenticity is verified via the gateway's signature/hash per their integration spec. On success: updates `payments.status`, `payments.raw_response`, moves the order to `confirmed`, and releases reserved inventory into a deduction (reserved → sold). On failure: marks payment `failed`; order stays `awaiting_payment` so the customer can retry via `POST /payments/initiate` again.

Always responds `200` to the gateway (even on internal processing issues, logged separately) to prevent the provider from endlessly retrying a webhook it can't tell apart from a real failure.

---

### `PATCH /admin/orders/{id}/status`
**Admin (Order Manager+)** · Maps to US-ORD-002/003, BR-ORD-003

Request: `{ "status": "confirmed" | "packed" | "shipped" | "delivered" | "cancelled" }`

Enforces the order lifecycle from BR-ORD-003 — only forward transitions are allowed (e.g. `packed` → `shipped` is valid, `shipped` → `pending` is not), and `cancelled` is only reachable before `shipped`. Cancelling releases reserved/sold inventory back to stock.

---

### `POST /admin/orders/{id}/refund`
**Admin (Order Manager+)** · Maps to US-PAY-005, BR-ORD-003 ("refunds require business approval")

Request: `{ "payment_id": "...", "amount": 1500.00, "reason": "..." }`

Creates a `refunds` row in `requested` status — this endpoint records the request, it does not itself move money. A separate approval step (`PATCH /admin/refunds/{id}` — approve/reject, omitted from the inventory table above as a straightforward status-only endpoint) triggers the actual gateway refund call once approved.

---

### `POST /coupons/validate`
**Public/Customer** · Maps to US-CHK-005, Promotion Rules (BRD §17)

Request: `{ "code": "CHESS10", "cart_total": 4500.00 }`

Validates: exists, `is_active`, within `starts_at`/`expires_at`, `usage_count < usage_limit`, `cart_total >= min_purchase_amount`. Response `200`: `{ "valid": true, "discount_amount": 450.00 }` or `422 INVALID_COUPON` with a specific reason code (`EXPIRED`, `USAGE_LIMIT_REACHED`, `MIN_PURCHASE_NOT_MET`).

---

### `PATCH /admin/inventory/{variantId}/adjust`
**Admin (Inventory Manager+)** · Maps to US-INV-001, BR-INV-003

Request: `{ "change_type": "restock" | "damage" | "adjustment", "quantity_delta": 20, "note": "..." }`

Writes an `inventory_transactions` row and updates `inventory.quantity_on_hand` in the same transaction — never edits the stock count directly, so every change stays traceable (NFR-AUD-001). Rejects a delta that would take `quantity_on_hand` negative (`422 NEGATIVE_STOCK`).

---

## 5. Traceability Summary

| Layer | Coverage |
| --- | --- |
| SRS Functional Modules | 16 of 16 non-vendor modules represented (AUTH, CUS, CAT, SCH, CRT, ORD, PAY, SHP, INV, REV, WSH, CMS, NOT, ADM, RPT — VND excluded, V3 scope) |
| Product Backlog Epics | EP-01 through EP-17 covered; EP-18 (Vendor Marketplace) excluded, matching ERD scope |
| Endpoint count | ~80, of which ~14 are V2-scope (marked inline) |

---

## 6. Open Questions for Implementation

* **Guest cart merge on login:** confirm the merge rule when a guest cart and an existing customer cart both have items for the same variant (sum quantities vs. keep the larger vs. prompt the user) — currently unspecified.
* **Refund approval endpoint:** `PATCH /admin/refunds/{id}` was named but not detailed above; needs its own status-transition rules once refund gateway integration is scoped.
* **SSLCommerz webhook contract:** exact payload/signature scheme depends on their current API docs at integration time — the shape assumed above is illustrative, not final.
* **Search relevance:** `sort=best_selling` and `sort=rating` require aggregated data (order counts, review averages) that may be precomputed on a schedule rather than calculated per-request, for performance at scale.

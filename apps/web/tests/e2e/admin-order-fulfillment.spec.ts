import { test, expect } from "@playwright/test";
import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  API_BASE_URL,
  adminLogin,
  createStockedProduct,
  inlineAddress,
} from "./fixtures";

/** Places a guest COD order directly via the API — this spec is about the
 * admin fulfilling an order, not about re-driving the storefront checkout
 * flow already covered by guest-checkout.spec.ts. */
async function placeGuestCodOrder(
  request: import("@playwright/test").APIRequestContext,
  variantId: string,
): Promise<string> {
  const address = inlineAddress();
  // Uses the test's own request context directly (rather than a fresh
  // one) so the guest-cart cookie the first call receives is sent back
  // on the second — Playwright's APIRequestContext keeps a per-host
  // cookie jar regardless of the config's frontend baseURL, since both
  // calls target the full API_BASE_URL explicitly.
  await request.post(`${API_BASE_URL}/cart/items`, {
    data: { product_variant_id: variantId, quantity: 1 },
  });
  const orderResponse = await request.post(`${API_BASE_URL}/orders`, {
    headers: { "Idempotency-Key": crypto.randomUUID() },
    data: {
      address: {
        recipient_name: address.recipientName,
        phone: address.phone,
        address_line1: address.addressLine1,
        city: address.city,
        district: address.district,
        country: "BD",
      },
      shipping_method: "standard",
      payment_method: "cod",
      guest_email: `e2e-fulfillment-${Date.now()}@example.com`,
    },
  });
  const body = await orderResponse.json();
  return body.data.order.order_number as string;
}

test("admin can fulfill an order by advancing its status", async ({
  page,
  request,
}) => {
  const adminToken = await adminLogin(request);
  const product = await createStockedProduct(request, adminToken);
  const orderNumber = await placeGuestCodOrder(request, product.variantId);

  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);

  await page.goto("/admin/orders");
  await page.getByRole("link", { name: orderNumber }).click();
  await expect(page).toHaveURL(/\/admin\/orders\/[^/]+$/);
  await expect(
    page.getByRole("heading", { name: `Order ${orderNumber}` }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Mark as Confirmed" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm" })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();

  // Confirming the order advances its available next action from
  // "Mark as Confirmed" to "Mark as Packed" — a stronger check than
  // just looking for the word "Confirmed" somewhere on the page, which
  // is ambiguous with the just-closed confirmation dialog's own heading.
  await expect(
    page.getByRole("button", { name: "Mark as Packed" }),
  ).toBeVisible();
});

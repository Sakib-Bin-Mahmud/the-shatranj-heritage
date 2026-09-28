import { test, expect } from "@playwright/test";
import {
  adminLogin,
  createStockedProduct,
  inlineAddress,
  uniqueSuffix,
} from "./fixtures";

test("guest can browse, add to cart, and complete a COD checkout", async ({
  page,
  request,
}) => {
  const adminToken = await adminLogin(request);
  const product = await createStockedProduct(request, adminToken);
  const address = inlineAddress();
  const guestEmail = `e2e-guest-${uniqueSuffix()}@example.com`;

  await page.goto(`/products/${product.slug}`);
  await expect(page.getByRole("heading", { name: product.name })).toBeVisible();
  await page.getByRole("button", { name: "Add to cart" }).click();
  await expect(page.getByText("Added to cart")).toBeVisible();

  await page.goto("/cart");
  await expect(page.getByText(product.name)).toBeVisible();
  await page.getByRole("button", { name: "Proceed to checkout" }).click();

  await expect(page).toHaveURL(/\/checkout$/);
  await page.getByLabel("Email address").fill(guestEmail);
  await page.getByLabel("Recipient name").fill(address.recipientName);
  await page.getByLabel("Phone").fill(address.phone);
  await page.getByLabel("Address line 1").fill(address.addressLine1);
  await page.getByLabel("City").fill(address.city);
  await page.getByLabel("District").fill(address.district);
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(
    page.getByRole("heading", { name: "Shipping method" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(
    page.getByRole("heading", { name: "Payment method" }),
  ).toBeVisible();
  await page.getByText("Cash on delivery").click();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(
    page.getByRole("heading", { name: "Review your order" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Place order" }).click();

  await expect(page).toHaveURL(/\/checkout\/confirmation\?order=.+status=cod/);
  await expect(
    page.getByRole("heading", { name: "Order placed" }),
  ).toBeVisible();
  await expect(page.getByText("Order number")).toBeVisible();
});

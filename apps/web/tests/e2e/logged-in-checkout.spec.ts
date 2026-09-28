import { test, expect } from "@playwright/test";
import {
  adminLogin,
  createStockedProduct,
  inlineAddress,
  uniqueSuffix,
} from "./fixtures";

test("logged-in customer can register, add to cart, and complete a COD checkout", async ({
  page,
  request,
}) => {
  const adminToken = await adminLogin(request);
  const product = await createStockedProduct(request, adminToken);
  const address = inlineAddress();
  const suffix = uniqueSuffix();

  await page.goto("/register");
  await page.getByLabel("Full name").fill("E2E Customer");
  await page
    .getByLabel("Email address")
    .fill(`e2e-customer-${suffix}@example.com`);
  await page.getByLabel("Password").fill("Passw0rd1234");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/account$/);

  await page.goto(`/products/${product.slug}`);
  await page.getByRole("button", { name: "Add to cart" }).click();
  await expect(page.getByText("Added to cart")).toBeVisible();

  await page.goto("/cart");
  await page.getByRole("button", { name: "Proceed to checkout" }).click();

  await expect(page).toHaveURL(/\/checkout$/);
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
  await expect(
    page.getByRole("link", { name: "View my orders" }),
  ).toBeVisible();
});

import { test, expect } from "@playwright/test";
import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  API_BASE_URL,
  adminLogin,
  uniqueSuffix,
} from "./fixtures";

test("admin can log in and create a new product", async ({ page, request }) => {
  const suffix = uniqueSuffix();
  const productName = `Admin E2E Product ${suffix}`;

  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);

  // A category must exist for the product form's required Category
  // select — created directly via the admin API (its own token, since
  // the UI never exposes the access token it holds in memory) rather
  // than through the Content admin page, since category creation is
  // exercised by its own F6 flow and isn't what this golden path checks.
  const adminAccessToken = await adminLogin(request);
  const category = await (
    await request.post(`${API_BASE_URL}/admin/categories`, {
      headers: { Authorization: `Bearer ${adminAccessToken}` },
      data: {
        name: `Admin E2E Category ${suffix}`,
        slug: `admin-e2e-category-${suffix}`,
      },
    })
  ).json();

  await page.goto("/admin/products/new");
  await page.getByLabel("Name").fill(productName);
  await page.getByLabel("SKU").fill(`ADMIN-E2E-${suffix}`);
  await page.getByLabel("Category").selectOption(category.data.id);
  await page.getByLabel("Base price (৳)").fill("2500");
  await page.getByRole("button", { name: "Create product" }).click();

  await expect(page).toHaveURL(/\/admin\/products\/[^/]+$/);
  await expect(page.getByRole("heading", { name: productName })).toBeVisible();
});

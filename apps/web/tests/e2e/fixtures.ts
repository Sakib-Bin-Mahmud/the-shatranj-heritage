import type { APIRequestContext } from "@playwright/test";

export const API_BASE_URL =
  process.env.PLAYWRIGHT_API_URL ?? "http://localhost:8000/api/v1";

export const ADMIN_EMAIL =
  process.env.ADMIN_E2E_EMAIL ?? "f7-super@example.com";
export const ADMIN_PASSWORD = process.env.ADMIN_E2E_PASSWORD ?? "Passw0rd1234";

export function uniqueSuffix(): string {
  return Math.random().toString(36).slice(2, 10);
}

async function json<T>(response: {
  json: () => Promise<unknown>;
  ok: () => boolean;
  status: () => number;
  url: () => string;
}): Promise<T> {
  if (!response.ok()) {
    throw new Error(
      `Request to ${response.url()} failed with ${response.status()}: ${JSON.stringify(await response.json())}`,
    );
  }
  const body = (await response.json()) as { data: T };
  return body.data;
}

// The admin login endpoint is rate-limited (10 requests/60s — a real
// brute-force guard, not something to work around). The config runs all
// spec files in a single worker, so caching the token module-wide keeps
// this suite's API-side setup calls down to one login per run, leaving
// headroom for the specs that also log in through the browser UI itself.
let cachedAdminToken: Promise<string> | null = null;

export async function adminLogin(request: APIRequestContext): Promise<string> {
  cachedAdminToken ??= (async () => {
    const response = await request.post(`${API_BASE_URL}/admin/auth/login`, {
      data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
    });
    const data = await json<{ access_token: string }>(response);
    return data.access_token;
  })();
  return cachedAdminToken;
}

/** Creates a fresh category + active product + in-stock variant via the
 * admin API, so checkout specs never depend on whatever products happen
 * to already exist in the database. Mirrors the backend test suite's own
 * `setup_stocked_variant` helper (apps/api/tests/test_shipping.py). */
export async function createStockedProduct(
  request: APIRequestContext,
  adminToken: string,
  options: { stock?: number } = {},
): Promise<{
  slug: string;
  productId: string;
  variantId: string;
  name: string;
}> {
  const headers = { Authorization: `Bearer ${adminToken}` };
  const suffix = uniqueSuffix();

  const category = await json<{ id: string }>(
    await request.post(`${API_BASE_URL}/admin/categories`, {
      headers,
      data: { name: `E2E Category ${suffix}`, slug: `e2e-category-${suffix}` },
    }),
  );

  const productName = `E2E Product ${suffix}`;
  const product = await json<{ id: string; slug: string }>(
    await request.post(`${API_BASE_URL}/admin/products`, {
      headers,
      data: {
        sku: `E2E-SKU-${suffix}`,
        name: productName,
        slug: `e2e-product-${suffix}`,
        category_id: category.id,
        base_price: "1000.00",
        status: "active",
      },
    }),
  );

  const variantResult = await json<{ variants: { id: string }[] }>(
    await request.post(
      `${API_BASE_URL}/admin/products/${product.id}/variants`,
      {
        headers,
        data: { sku: `E2E-VAR-${suffix}`, variant_name: "Standard" },
      },
    ),
  );
  const variant = variantResult.variants[variantResult.variants.length - 1];

  await json(
    await request.patch(
      `${API_BASE_URL}/admin/inventory/${variant.id}/adjust`,
      {
        headers,
        data: {
          change_type: "restock",
          quantity_delta: options.stock ?? 10,
          note: "e2e restock",
        },
      },
    ),
  );

  return {
    slug: product.slug,
    productId: product.id,
    variantId: variant.id,
    name: productName,
  };
}

export function inlineAddress(overrides: Partial<Record<string, string>> = {}) {
  return {
    recipientName: "Karim Ahmed",
    phone: "01711111111",
    addressLine1: "House 12, Road 5",
    city: "Dhaka",
    district: "Dhaka",
    ...overrides,
  };
}

import { apiFetch } from "@/lib/api-client";

export type CartItem = {
  id: string;
  product_variant_id: string;
  product_id: string | null;
  product_name: string | null;
  product_slug: string | null;
  sku: string | null;
  variant_name: string | null;
  primary_image_url: string | null;
  quantity: number;
  unit_price_snapshot: string;
  line_total: string;
  max_available: number;
  is_available: boolean;
};

export type Cart = {
  id: string;
  item_count: number;
  items: CartItem[];
  subtotal: string;
  estimated_shipping: string;
  estimated_tax: string;
  discount_amount: string;
  total: string;
  warnings: string[];
};

// Guest carts are identified by an httpOnly cookie the API sets itself;
// `credentials: "include"` (already the default fetch behavior for
// same-origin requests via apiFetch) is what lets that round-trip.

export function getCart(accessToken?: string | null): Promise<Cart> {
  return apiFetch<Cart>("/cart", { accessToken });
}

export function addCartItem(
  input: { product_variant_id: string; quantity?: number },
  accessToken?: string | null,
): Promise<Cart> {
  return apiFetch<Cart>("/cart/items", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function updateCartItem(
  itemId: string,
  quantity: number,
  accessToken?: string | null,
): Promise<Cart> {
  return apiFetch<Cart>(`/cart/items/${encodeURIComponent(itemId)}`, {
    method: "PATCH",
    body: { quantity },
    accessToken,
  });
}

export function removeCartItem(
  itemId: string,
  accessToken?: string | null,
): Promise<Cart> {
  return apiFetch<Cart>(`/cart/items/${encodeURIComponent(itemId)}`, {
    method: "DELETE",
    accessToken,
  });
}

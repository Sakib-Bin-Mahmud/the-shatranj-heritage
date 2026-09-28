import { apiFetch } from "@/lib/api-client";
import type { Paginated } from "./types";

export type InventoryItem = {
  id: string;
  product_variant_id: string;
  variant_sku: string;
  variant_name: string;
  product_name: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_threshold: number;
  is_low_stock: boolean;
};

export type InventoryTransaction = {
  id: string;
  product_variant_id: string;
  change_type: string;
  quantity_delta: number;
  reference_type: string | null;
  reference_id: string | null;
  note: string | null;
  created_by: string | null;
  created_at: string;
};

export type AdjustInventoryInput = {
  change_type: "restock" | "damage" | "adjustment";
  quantity_delta: number;
  note?: string | null;
};

export type AdjustInventoryResult = {
  id: string;
  product_variant_id: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
};

export function listInventory(
  params: { low_stock?: boolean; page?: number; limit?: number } = {},
  accessToken?: string | null,
): Promise<Paginated<InventoryItem>> {
  const search = new URLSearchParams();
  if (params.low_stock) search.set("low_stock", "true");
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiFetch<Paginated<InventoryItem>>(
    `/admin/inventory${query ? `?${query}` : ""}`,
    { accessToken },
  );
}

export function adjustInventory(
  variantId: string,
  input: AdjustInventoryInput,
  accessToken?: string | null,
): Promise<AdjustInventoryResult> {
  return apiFetch<AdjustInventoryResult>(
    `/admin/inventory/${encodeURIComponent(variantId)}/adjust`,
    { method: "PATCH", body: input, accessToken },
  );
}

export function listInventoryTransactions(
  variantId: string,
  params: { page?: number; limit?: number } = {},
  accessToken?: string | null,
): Promise<Paginated<InventoryTransaction>> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiFetch<Paginated<InventoryTransaction>>(
    `/admin/inventory/${encodeURIComponent(variantId)}/transactions${query ? `?${query}` : ""}`,
    { accessToken },
  );
}

import { apiFetch } from "@/lib/api-client";

export type ShippingRate = {
  id: string;
  zone: string;
  method: string;
  base_rate: string;
  base_weight_grams: number;
  per_kg_rate: string;
  is_active: boolean;
};

export function adminListShippingRates(
  accessToken?: string | null,
): Promise<ShippingRate[]> {
  return apiFetch<ShippingRate[]>("/admin/settings/shipping-rates", {
    accessToken,
  });
}

export function adminUpdateShippingRate(
  rateId: string,
  input: {
    base_rate?: string;
    base_weight_grams?: number;
    per_kg_rate?: string;
    is_active?: boolean;
  },
  accessToken?: string | null,
): Promise<ShippingRate> {
  return apiFetch<ShippingRate>(
    `/admin/settings/shipping-rates/${encodeURIComponent(rateId)}`,
    { method: "PATCH", body: input, accessToken },
  );
}

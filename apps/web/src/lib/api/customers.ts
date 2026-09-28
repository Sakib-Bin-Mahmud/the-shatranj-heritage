import { apiFetch } from "@/lib/api-client";
import type { AddressInput } from "./orders";
import type { Paginated } from "./types";

export type Address = AddressInput & {
  id: string;
  customer_id: string;
  label: string | null;
  country: string;
  is_default: boolean;
};

export function listMyAddresses(
  accessToken?: string | null,
): Promise<Address[]> {
  return apiFetch<Address[]>("/customers/me/addresses", { accessToken });
}

// --- Admin -------------------------------------------------------------

export type CustomerProfile = {
  id: string;
  email: string | null;
  mobile_number: string | null;
  full_name: string;
  preferred_language: string;
  status: "active" | "inactive" | "suspended";
};

export function adminListCustomers(
  params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: "active" | "inactive" | "suspended";
  } = {},
  accessToken?: string | null,
): Promise<Paginated<CustomerProfile>> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  if (params.search) search.set("search", params.search);
  if (params.status) search.set("status", params.status);
  const query = search.toString();
  return apiFetch<Paginated<CustomerProfile>>(
    `/admin/customers${query ? `?${query}` : ""}`,
    { accessToken },
  );
}

export function adminGetCustomer(
  customerId: string,
  accessToken?: string | null,
): Promise<CustomerProfile> {
  return apiFetch<CustomerProfile>(
    `/admin/customers/${encodeURIComponent(customerId)}`,
    { accessToken },
  );
}

export function adminUpdateCustomerStatus(
  customerId: string,
  status: "active" | "inactive" | "suspended",
  accessToken?: string | null,
): Promise<CustomerProfile> {
  return apiFetch<CustomerProfile>(
    `/admin/customers/${encodeURIComponent(customerId)}/status`,
    { method: "PATCH", body: { status }, accessToken },
  );
}

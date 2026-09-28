import { apiFetch } from "@/lib/api-client";
import type { Paginated } from "./types";

export type Role = {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
};

export type StaffSummary = {
  id: string;
  email: string;
  full_name: string;
  status: string;
  roles: string[];
};

export type AuditLogEntry = {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  created_at: string;
};

export type ShippingRate = {
  id: string;
  zone: string;
  method: string;
  base_rate: string;
  base_weight_grams: number;
  per_kg_rate: string;
  is_active: boolean;
};

function paginationQuery(params: { page?: number; limit?: number }): string {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listRoles(accessToken?: string | null): Promise<Role[]> {
  return apiFetch<Role[]>("/admin/roles", { accessToken });
}

export function listStaff(
  params: { page?: number; limit?: number } = {},
  accessToken?: string | null,
): Promise<Paginated<StaffSummary>> {
  return apiFetch<Paginated<StaffSummary>>(
    `/admin/users${paginationQuery(params)}`,
    { accessToken },
  );
}

export function createStaff(
  input: {
    email: string;
    password: string;
    full_name: string;
    role_names: string[];
  },
  accessToken?: string | null,
): Promise<StaffSummary> {
  return apiFetch<StaffSummary>("/admin/users", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function assignStaffRoles(
  staffId: string,
  roleNames: string[],
  accessToken?: string | null,
): Promise<StaffSummary> {
  return apiFetch<StaffSummary>(
    `/admin/users/${encodeURIComponent(staffId)}/roles`,
    { method: "PATCH", body: { role_names: roleNames }, accessToken },
  );
}

export function listAuditLogs(
  params: { page?: number; limit?: number; entity_type?: string } = {},
  accessToken?: string | null,
): Promise<Paginated<AuditLogEntry>> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  if (params.entity_type) search.set("entity_type", params.entity_type);
  const query = search.toString();
  return apiFetch<Paginated<AuditLogEntry>>(
    `/admin/audit-logs${query ? `?${query}` : ""}`,
    { accessToken },
  );
}

export function listShippingRates(
  accessToken?: string | null,
): Promise<ShippingRate[]> {
  return apiFetch<ShippingRate[]>("/admin/settings/shipping-rates", {
    accessToken,
  });
}

export function updateShippingRate(
  rateId: string,
  input: Partial<{
    base_rate: string;
    base_weight_grams: number;
    per_kg_rate: string;
    is_active: boolean;
  }>,
  accessToken?: string | null,
): Promise<ShippingRate> {
  return apiFetch<ShippingRate>(
    `/admin/settings/shipping-rates/${encodeURIComponent(rateId)}`,
    { method: "PATCH", body: input, accessToken },
  );
}

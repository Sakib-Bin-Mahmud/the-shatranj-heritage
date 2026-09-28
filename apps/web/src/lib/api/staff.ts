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
  status: "active" | "inactive" | "suspended";
  roles: string[];
};

export function adminListRoles(accessToken?: string | null): Promise<Role[]> {
  return apiFetch<Role[]>("/admin/roles", { accessToken });
}

export function adminListStaff(
  params: { page?: number; limit?: number } = {},
  accessToken?: string | null,
): Promise<Paginated<StaffSummary>> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiFetch<Paginated<StaffSummary>>(
    `/admin/users${query ? `?${query}` : ""}`,
    { accessToken },
  );
}

export function adminCreateStaff(
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

export function adminAssignStaffRoles(
  staffId: string,
  roleNames: string[],
  accessToken?: string | null,
): Promise<StaffSummary> {
  return apiFetch<StaffSummary>(
    `/admin/users/${encodeURIComponent(staffId)}/roles`,
    { method: "PATCH", body: { role_names: roleNames }, accessToken },
  );
}

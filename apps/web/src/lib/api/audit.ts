import { apiFetch } from "@/lib/api-client";
import type { Paginated } from "./types";

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

export function adminListAuditLogs(
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

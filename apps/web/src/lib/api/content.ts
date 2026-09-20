import { apiFetch } from "@/lib/api-client";

export type PageSummary = {
  id: string;
  slug: string;
  title: string;
  page_type: string;
  is_published: boolean;
  published_at: string | null;
};

export type PageDetail = PageSummary & {
  body: string;
};

export function listContentPages(): Promise<PageSummary[]> {
  return apiFetch<PageSummary[]>("/content/pages");
}

export function getContentPage(slug: string): Promise<PageDetail> {
  return apiFetch<PageDetail>(`/content/pages/${encodeURIComponent(slug)}`);
}

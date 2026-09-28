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

// --- Admin -----------------------------------------------------------------

export type PageInput = {
  slug: string;
  title: string;
  body: string;
  page_type?: "page" | "faq" | "policy";
  is_published?: boolean;
};

export function adminListContentPages(
  accessToken?: string | null,
): Promise<PageSummary[]> {
  return apiFetch<PageSummary[]>("/admin/content/pages", { accessToken });
}

export function adminGetContentPage(
  pageId: string,
  accessToken?: string | null,
): Promise<PageDetail> {
  return apiFetch<PageDetail>(
    `/admin/content/pages/${encodeURIComponent(pageId)}`,
    { accessToken },
  );
}

export function adminCreateContentPage(
  input: PageInput,
  accessToken?: string | null,
): Promise<PageDetail> {
  return apiFetch<PageDetail>("/admin/content/pages", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function adminUpdateContentPage(
  pageId: string,
  input: Partial<Omit<PageInput, "slug">>,
  accessToken?: string | null,
): Promise<PageDetail> {
  return apiFetch<PageDetail>(
    `/admin/content/pages/${encodeURIComponent(pageId)}`,
    { method: "PATCH", body: input, accessToken },
  );
}

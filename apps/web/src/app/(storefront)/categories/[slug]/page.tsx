import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getCategory, listProducts } from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import { CategoryDetailContent } from "./category-detail-content";

type Params = { slug: string };
type SearchParams = { page?: string };

// Live catalog data — never prerender against build-time API state.
export const dynamic = "force-dynamic";

const PAGE_SIZE = 20;

async function loadCategory(slug: string) {
  try {
    return await getCategory(slug);
  } catch (error) {
    if (error instanceof ApiClientError && error.code === "NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  const category = await loadCategory(slug);
  if (!category) return {};
  return { title: `${category.name} — The Shatranj Heritage` };
}

export default async function CategoryDetailPage({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await params;
  const { page: pageParam } = await searchParams;
  const category = await loadCategory(slug);
  if (!category) notFound();

  const page = Number(pageParam ?? "1") || 1;
  const { items, meta } = await listProducts({
    category: slug,
    page,
    limit: PAGE_SIZE,
  });

  return (
    <CategoryDetailContent
      category={category}
      slug={slug}
      items={items}
      meta={meta}
    />
  );
}

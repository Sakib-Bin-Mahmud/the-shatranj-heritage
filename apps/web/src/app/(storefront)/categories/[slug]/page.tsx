import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getCategory, listProducts } from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import { ProductCard } from "@/components/product-card";
import { EmptyState } from "@/components/ui";
import styles from "./page.module.css";

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
    <div className={styles.page}>
      <div className={styles.header}>
        <Link href="/products">All products</Link>
        <h1>{category.name}</h1>
        {category.description && <p>{category.description}</p>}
      </div>

      {items.length === 0 ? (
        <EmptyState title="No products in this category yet" />
      ) : (
        <>
          <div className={styles.grid}>
            {items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {meta.total_pages > 1 && (
            <nav className={styles.pagination} aria-label="Pagination">
              <span>
                Page {meta.page} of {meta.total_pages}
              </span>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                {meta.page > 1 && (
                  <Link href={`/categories/${slug}?page=${meta.page - 1}`}>
                    Previous
                  </Link>
                )}
                {meta.page < meta.total_pages && (
                  <Link href={`/categories/${slug}?page=${meta.page + 1}`}>
                    Next
                  </Link>
                )}
              </div>
            </nav>
          )}
        </>
      )}
    </div>
  );
}

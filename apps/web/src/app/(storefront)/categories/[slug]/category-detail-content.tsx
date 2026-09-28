"use client";

import Link from "next/link";
import { useDictionary } from "@/i18n/dictionary-context";
import type { Category, ProductSummary } from "@/lib/api/catalog";
import { ProductCard } from "@/components/product-card";
import { EmptyState } from "@/components/ui";
import styles from "./page.module.css";

export function CategoryDetailContent({
  category,
  slug,
  items,
  meta,
}: {
  category: Category;
  slug: string;
  items: ProductSummary[];
  meta: { page: number; total_pages: number };
}) {
  const { dict } = useDictionary();

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <Link href="/products">{dict.catalog.category.backToAll}</Link>
        <h1>{category.name}</h1>
        {category.description && <p>{category.description}</p>}
      </div>

      {items.length === 0 ? (
        <EmptyState title={dict.catalog.category.emptyHeading} />
      ) : (
        <>
          <div className={styles.grid}>
            {items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {meta.total_pages > 1 && (
            <nav
              className={styles.pagination}
              aria-label={dict.common.pagination.label}
            >
              <span role="status" aria-live="polite">
                {dict.common.pagination.pageOf
                  .replace("{page}", String(meta.page))
                  .replace("{totalPages}", String(meta.total_pages))}
              </span>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                {meta.page > 1 && (
                  <Link href={`/categories/${slug}?page=${meta.page - 1}`}>
                    {dict.common.pagination.previous}
                  </Link>
                )}
                {meta.page < meta.total_pages && (
                  <Link href={`/categories/${slug}?page=${meta.page + 1}`}>
                    {dict.common.pagination.next}
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

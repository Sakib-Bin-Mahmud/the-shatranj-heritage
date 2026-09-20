"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { ProductCard } from "@/components/product-card";
import { CategoryTree } from "@/components/category-tree";
import { EmptyState, Pagination, SelectField, Skeleton } from "@/components/ui";
import {
  listCategories,
  listProducts,
  type ProductListParams,
} from "@/lib/api/catalog";
import { ProductFilters, type FilterFormValues } from "./product-filters";
import styles from "./page.module.css";

const PAGE_SIZE = 20;

function paramsFromSearch(searchParams: URLSearchParams): ProductListParams {
  const page = Number(searchParams.get("page") ?? "1");
  const priceMin = searchParams.get("price_min");
  const priceMax = searchParams.get("price_max");
  return {
    q: searchParams.get("q") ?? undefined,
    category: searchParams.get("category") ?? undefined,
    price_min: priceMin ? Number(priceMin) : undefined,
    price_max: priceMax ? Number(priceMax) : undefined,
    material: searchParams.get("material") ?? undefined,
    availability:
      searchParams.get("availability") === "in_stock" ? "in_stock" : "all",
    featured: searchParams.get("featured") === "true" ? true : undefined,
    sort: (searchParams.get("sort") as ProductListParams["sort"]) ?? undefined,
    page: Number.isFinite(page) && page > 0 ? page : 1,
    limit: PAGE_SIZE,
  };
}

function buildHref(
  current: URLSearchParams,
  overrides: Record<string, string | number | boolean | undefined>,
): string {
  const next = new URLSearchParams(current.toString());
  for (const [key, value] of Object.entries(overrides)) {
    if (value === undefined || value === "") next.delete(key);
    else next.set(key, String(value));
  }
  if (!("page" in overrides)) next.delete("page");
  const query = next.toString();
  return query ? `/products?${query}` : "/products";
}

export function ProductsContent() {
  const { dict } = useDictionary();
  const t = dict.catalog;
  const router = useRouter();
  const searchParams = useSearchParams();
  const filters = paramsFromSearch(searchParams);

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: listCategories,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["products", filters],
    queryFn: () => listProducts(filters),
  });

  function navigate(
    overrides: Record<string, string | number | boolean | undefined>,
  ) {
    router.push(buildHref(searchParams, overrides));
  }

  function handleApplyFilters(values: FilterFormValues) {
    navigate({
      q: values.q,
      price_min: values.price_min,
      price_max: values.price_max,
      material: values.material,
      availability: values.availability === "in_stock" ? "in_stock" : undefined,
      featured: values.featured ? true : undefined,
    });
  }

  const items = data?.items ?? [];
  const meta = data?.meta;
  const suggestions = data?.suggestions;

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <ProductFilters initial={filters} onApply={handleApplyFilters} />

        {categories && categories.length > 0 && (
          <div className={styles.filterGroup}>
            <span className={styles.filterHeading}>
              {t.filters.categoryLabel}
            </span>
            <CategoryTree
              categories={categories}
              activeSlug={filters.category}
              linkTo={(slug) => `/categories/${slug}`}
            />
          </div>
        )}
      </aside>

      <div className={styles.main}>
        <div className={styles.headerRow}>
          <h1>{t.listing.heading}</h1>
          <div className={styles.sortRow}>
            <SelectField
              label={t.filters.sortLabel}
              value={filters.sort ?? ""}
              onChange={(e) => navigate({ sort: e.target.value || undefined })}
            >
              <option value="">{t.filters.sortRelevance}</option>
              <option value="price_asc">{t.filters.sortPriceAsc}</option>
              <option value="price_desc">{t.filters.sortPriceDesc}</option>
              <option value="newest">{t.filters.sortNewest}</option>
              <option value="best_selling">{t.filters.sortBestSelling}</option>
              <option value="rating">{t.filters.sortRating}</option>
              <option value="alphabetical">{t.filters.sortAlphabetical}</option>
            </SelectField>
          </div>
        </div>

        {meta && (
          <span className={styles.resultsCount}>
            {t.listing.resultsCount.replace("{count}", String(meta.total))}
          </span>
        )}

        {isLoading ? (
          <div className={styles.grid}>
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} height="16rem" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className={styles.suggestions}>
            <EmptyState
              title={t.listing.noResultsHeading}
              description={t.listing.noResultsBody}
            />

            {suggestions && suggestions.categories.length > 0 && (
              <div>
                <span className={styles.suggestionsHeading}>
                  {t.listing.suggestedCategoriesHeading}
                </span>
                <div className={styles.suggestionsCategoryList}>
                  {suggestions.categories.map((category) => (
                    <Link
                      key={category.id}
                      href={buildHref(searchParams, {
                        category: category.slug,
                        q: undefined,
                      })}
                    >
                      {category.name}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {suggestions && suggestions.featured_products.length > 0 && (
              <div>
                <span className={styles.suggestionsHeading}>
                  {t.listing.suggestedProductsHeading}
                </span>
                <div className={styles.grid}>
                  {suggestions.featured_products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className={styles.grid}>
              {items.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
            {meta && meta.total_pages > 1 && (
              <Pagination
                page={meta.page}
                totalPages={meta.total_pages}
                onPageChange={(page) => navigate({ page })}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

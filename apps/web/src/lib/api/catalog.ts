import { apiFetch } from "@/lib/api-client";
import type { Paginated } from "./types";

export type Category = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  image_url: string | null;
  sort_order: number;
  parent_category_id: string | null;
  is_active: boolean;
};

export type CategoryTree = Category & { children: CategoryTree[] };

export type Artisan = {
  id: string;
  name: string;
  region: string | null;
  bio: string | null;
  photo_url: string | null;
};

export type ProductVariant = {
  id: string;
  product_id: string;
  sku: string;
  variant_name: string;
  price_override: string | null;
  weight_grams: number | null;
  attributes: Record<string, unknown>;
  is_default: boolean;
  status: string;
  effective_price: string;
  quantity_available: number;
};

export type ProductImage = {
  id: string;
  product_id: string;
  product_variant_id: string | null;
  url: string;
  alt_text: string | null;
  sort_order: number;
  is_primary: boolean;
};

export type ProductSummary = {
  id: string;
  slug: string;
  name: string;
  primary_image_url: string | null;
  price: string;
  stock_status: string;
  is_featured: boolean;
};

export type ProductDetail = {
  id: string;
  sku: string;
  name: string;
  slug: string;
  description: string | null;
  category: Category;
  artisan: Artisan | null;
  brand: string | null;
  base_price: string;
  currency: string;
  weight_grams: number | null;
  status: string;
  is_featured: boolean;
  variants: ProductVariant[];
  images: ProductImage[];
};

export type SearchSuggestions = {
  categories: Category[];
  featured_products: ProductSummary[];
};

export type ProductListResponse = Paginated<ProductSummary> & {
  suggestions?: SearchSuggestions;
};

export type ProductListParams = {
  q?: string;
  category?: string;
  price_min?: number;
  price_max?: number;
  material?: string;
  availability?: "in_stock" | "all";
  featured?: boolean;
  sort?:
    | "relevance"
    | "price_asc"
    | "price_desc"
    | "newest"
    | "best_selling"
    | "rating"
    | "alphabetical";
  page?: number;
  limit?: number;
};

function toQueryString(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listCategories(): Promise<CategoryTree[]> {
  return apiFetch<CategoryTree[]>("/categories");
}

export function getCategory(slug: string): Promise<Category> {
  return apiFetch<Category>(`/categories/${encodeURIComponent(slug)}`);
}

export function listProducts(
  params: ProductListParams = {},
): Promise<ProductListResponse> {
  return apiFetch<ProductListResponse>(`/products${toQueryString(params)}`);
}

export function getProduct(slug: string): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/products/${encodeURIComponent(slug)}`);
}

export function getRelatedProducts(
  productId: string,
): Promise<ProductSummary[]> {
  return apiFetch<ProductSummary[]>(
    `/products/${encodeURIComponent(productId)}/related`,
  );
}

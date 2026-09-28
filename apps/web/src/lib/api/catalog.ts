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

// --- Admin: categories ----------------------------------------------------

export type CategoryInput = {
  name: string;
  slug: string;
  description?: string | null;
  image_url?: string | null;
  sort_order?: number;
  parent_category_id?: string | null;
};

export function adminListCategories(
  accessToken?: string | null,
): Promise<Category[]> {
  return apiFetch<Category[]>("/admin/categories", { accessToken });
}

export function adminCreateCategory(
  input: CategoryInput,
  accessToken?: string | null,
): Promise<Category> {
  return apiFetch<Category>("/admin/categories", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function adminUpdateCategory(
  categoryId: string,
  input: Partial<CategoryInput> & { is_active?: boolean },
  accessToken?: string | null,
): Promise<Category> {
  return apiFetch<Category>(
    `/admin/categories/${encodeURIComponent(categoryId)}`,
    { method: "PATCH", body: input, accessToken },
  );
}

export function adminDeactivateCategory(
  categoryId: string,
  accessToken?: string | null,
): Promise<Category> {
  return apiFetch<Category>(
    `/admin/categories/${encodeURIComponent(categoryId)}`,
    { method: "DELETE", accessToken },
  );
}

// --- Admin: artisans --------------------------------------------------------

export type ArtisanInput = {
  name: string;
  region?: string | null;
  bio?: string | null;
  photo_url?: string | null;
};

export function adminListArtisans(
  accessToken?: string | null,
): Promise<Artisan[]> {
  return apiFetch<Artisan[]>("/admin/artisans", { accessToken });
}

export function adminCreateArtisan(
  input: ArtisanInput,
  accessToken?: string | null,
): Promise<Artisan> {
  return apiFetch<Artisan>("/admin/artisans", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function adminUpdateArtisan(
  artisanId: string,
  input: Partial<ArtisanInput>,
  accessToken?: string | null,
): Promise<Artisan> {
  return apiFetch<Artisan>(`/admin/artisans/${encodeURIComponent(artisanId)}`, {
    method: "PATCH",
    body: input,
    accessToken,
  });
}

// --- Admin: products --------------------------------------------------------

export type ProductInput = {
  sku: string;
  name: string;
  slug: string;
  description?: string | null;
  category_id: string;
  artisan_id?: string | null;
  brand?: string | null;
  base_price: string;
  weight_grams?: number | null;
  status?: "draft" | "active" | "archived";
  meta_title?: string | null;
  meta_description?: string | null;
  is_featured?: boolean;
};

export type AdminProductListParams = {
  status?: "draft" | "active" | "archived";
  search?: string;
  page?: number;
  limit?: number;
};

export function adminListProducts(
  params: AdminProductListParams = {},
  accessToken?: string | null,
): Promise<Paginated<ProductDetail>> {
  return apiFetch<Paginated<ProductDetail>>(
    `/admin/products${toQueryString(params)}`,
    { accessToken },
  );
}

export function adminGetProduct(
  productId: string,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}`,
    { accessToken },
  );
}

export function adminCreateProduct(
  input: ProductInput,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>("/admin/products", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export function adminUpdateProduct(
  productId: string,
  input: Partial<ProductInput>,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}`,
    { method: "PATCH", body: input, accessToken },
  );
}

export function adminArchiveProduct(
  productId: string,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}`,
    { method: "DELETE", accessToken },
  );
}

// --- Admin: variants ---------------------------------------------------

export type VariantInput = {
  sku: string;
  variant_name: string;
  price_override?: string | null;
  weight_grams?: number | null;
  attributes?: Record<string, unknown>;
  is_default?: boolean;
};

export function adminCreateVariant(
  productId: string,
  input: VariantInput,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}/variants`,
    { method: "POST", body: input, accessToken },
  );
}

export function adminUpdateVariant(
  productId: string,
  variantId: string,
  input: Partial<VariantInput> & { status?: "active" | "archived" },
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}/variants/${encodeURIComponent(variantId)}`,
    { method: "PATCH", body: input, accessToken },
  );
}

export function adminArchiveVariant(
  productId: string,
  variantId: string,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}/variants/${encodeURIComponent(variantId)}`,
    { method: "DELETE", accessToken },
  );
}

// --- Admin: images -----------------------------------------------------

export function adminAddImage(
  productId: string,
  input: {
    file: File;
    altText?: string;
    isPrimary?: boolean;
    productVariantId?: string;
  },
  accessToken?: string | null,
): Promise<ProductDetail> {
  const formData = new FormData();
  formData.set("file", input.file);
  if (input.altText) formData.set("alt_text", input.altText);
  if (input.isPrimary) formData.set("is_primary", "true");
  if (input.productVariantId) {
    formData.set("product_variant_id", input.productVariantId);
  }
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}/images`,
    { method: "POST", body: formData, accessToken },
  );
}

export function adminDeleteImage(
  productId: string,
  imageId: string,
  accessToken?: string | null,
): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(
    `/admin/products/${encodeURIComponent(productId)}/images/${encodeURIComponent(imageId)}`,
    { method: "DELETE", accessToken },
  );
}

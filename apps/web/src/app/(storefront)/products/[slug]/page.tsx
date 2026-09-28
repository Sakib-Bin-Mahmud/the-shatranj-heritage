import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getProduct } from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import { ProductDetailClient } from "./product-detail-client";

type Params = { slug: string };

// Live catalog data (stock/price) — never prerender against build-time
// API state.
export const dynamic = "force-dynamic";

async function loadProduct(slug: string) {
  try {
    return await getProduct(slug);
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
  const product = await loadProduct(slug);
  if (!product) return {};
  return {
    title: `${product.name} — The Shatranj Heritage`,
    description: product.description ?? undefined,
  };
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { slug } = await params;
  const product = await loadProduct(slug);
  if (!product) notFound();

  return <ProductDetailClient initialProduct={product} />;
}

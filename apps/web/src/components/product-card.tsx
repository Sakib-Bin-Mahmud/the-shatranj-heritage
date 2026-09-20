"use client";

import Link from "next/link";
import { useDictionary } from "@/i18n/dictionary-context";
import { Badge, type BadgeTone } from "@/components/ui";
import type { ProductSummary } from "@/lib/api/catalog";
import styles from "./product-card.module.css";

const STOCK_TONE: Record<string, BadgeTone> = {
  in_stock: "success",
  low_stock: "warning",
  out_of_stock: "danger",
};

export function ProductCard({ product }: { product: ProductSummary }) {
  const { dict } = useDictionary();
  const stockLabel =
    product.stock_status === "in_stock"
      ? dict.catalog.stock.inStock
      : product.stock_status === "low_stock"
        ? dict.catalog.stock.lowStock
        : dict.catalog.stock.outOfStock;

  return (
    <Link href={`/products/${product.slug}`} className={styles.card}>
      <div className={styles.imageWrap}>
        {product.primary_image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.primary_image_url}
            alt={product.name}
            className={styles.image}
          />
        ) : (
          <span className={styles.imagePlaceholder} aria-hidden="true">
            ♞
          </span>
        )}
      </div>
      <span className={styles.name}>{product.name}</span>
      <div className={styles.priceRow}>
        <span className={styles.price}>৳{product.price}</span>
        <Badge tone={STOCK_TONE[product.stock_status] ?? "neutral"}>
          {stockLabel}
        </Badge>
      </div>
    </Link>
  );
}

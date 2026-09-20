"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { useAuth } from "@/lib/auth-context";
import {
  getProduct,
  getRelatedProducts,
  type ProductDetail,
  type ProductVariant,
} from "@/lib/api/catalog";
import { addCartItem } from "@/lib/api/cart";
import { ApiClientError } from "@/lib/api-client";
import { ProductCard } from "@/components/product-card";
import {
  Alert,
  Badge,
  Button,
  SelectField,
  TextField,
  type BadgeTone,
} from "@/components/ui";
import styles from "./page.module.css";

const STOCK_TONE: Record<string, BadgeTone> = {
  in_stock: "success",
  low_stock: "warning",
  out_of_stock: "danger",
};

function variantStockStatus(
  variant: ProductVariant,
): "in_stock" | "low_stock" | "out_of_stock" {
  if (variant.quantity_available <= 0) return "out_of_stock";
  if (variant.quantity_available <= 5) return "low_stock";
  return "in_stock";
}

function collectAttributeOptions(
  variants: ProductVariant[],
): Map<string, string[]> {
  const options = new Map<string, Set<string>>();
  for (const variant of variants) {
    for (const [key, value] of Object.entries(variant.attributes)) {
      if (typeof value !== "string") continue;
      if (!options.has(key)) options.set(key, new Set());
      options.get(key)!.add(value);
    }
  }
  const result = new Map<string, string[]>();
  for (const [key, values] of options) result.set(key, Array.from(values));
  return result;
}

function findMatchingVariant(
  variants: ProductVariant[],
  selection: Record<string, string>,
): ProductVariant | undefined {
  return variants.find((variant) =>
    Object.entries(selection).every(
      ([key, value]) => String(variant.attributes[key] ?? "") === value,
    ),
  );
}

export function ProductDetailClient({
  initialProduct,
}: {
  initialProduct: ProductDetail;
}) {
  const { dict } = useDictionary();
  const t = dict.catalog.product;
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();

  const { data: product = initialProduct } = useQuery({
    queryKey: ["product", initialProduct.slug],
    queryFn: () => getProduct(initialProduct.slug),
    initialData: initialProduct,
    refetchInterval: 30_000,
  });

  const attributeOptions = useMemo(
    () => collectAttributeOptions(product.variants),
    [product.variants],
  );

  const defaultVariant =
    product.variants.find((v) => v.is_default) ?? product.variants[0];

  const [selection, setSelection] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    if (defaultVariant) {
      for (const key of attributeOptions.keys()) {
        const value = defaultVariant.attributes[key];
        if (typeof value === "string") initial[key] = value;
      }
    }
    return initial;
  });

  const selectedVariant =
    findMatchingVariant(product.variants, selection) ?? defaultVariant;

  const [quantity, setQuantity] = useState(1);
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  const images = product.images.length > 0 ? product.images : [];
  const activeImage = images[activeImageIndex];

  const addToCart = useMutation({
    mutationFn: () =>
      addCartItem(
        { product_variant_id: selectedVariant!.id, quantity },
        accessToken,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    },
  });

  const stockStatus = selectedVariant
    ? variantStockStatus(selectedVariant)
    : "out_of_stock";
  const stockLabel =
    stockStatus === "in_stock"
      ? dict.catalog.stock.inStock
      : stockStatus === "low_stock"
        ? dict.catalog.stock.lowStock
        : dict.catalog.stock.outOfStock;

  return (
    <div className={styles.page}>
      <div className={styles.top}>
        <div className={styles.gallery}>
          <div className={styles.mainImageWrap}>
            {activeImage ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={activeImage.url}
                alt={activeImage.alt_text ?? product.name}
                className={styles.mainImage}
              />
            ) : (
              <span className={styles.mainImagePlaceholder} aria-hidden="true">
                ♞
              </span>
            )}
          </div>
          {images.length > 1 && (
            <div className={styles.thumbRow}>
              {images.map((image, index) => (
                <button
                  key={image.id}
                  type="button"
                  className={`${styles.thumb} ${index === activeImageIndex ? styles.thumbActive : ""}`}
                  onClick={() => setActiveImageIndex(index)}
                  aria-label={`View image ${index + 1}`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={image.url} alt="" className={styles.thumbImage} />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className={styles.info}>
          <span className={styles.sku}>
            {t.skuLabel}: {selectedVariant?.sku ?? product.sku}
          </span>
          <h1>{product.name}</h1>
          <div className={styles.priceRow}>
            <span>
              ৳{selectedVariant?.effective_price ?? product.base_price}
            </span>
            <Badge tone={STOCK_TONE[stockStatus]}>{stockLabel}</Badge>
          </div>

          {attributeOptions.size > 0 && (
            <div className={styles.variantSelectors}>
              {Array.from(attributeOptions.entries()).map(([key, values]) => (
                <SelectField
                  key={key}
                  label={key.charAt(0).toUpperCase() + key.slice(1)}
                  value={selection[key] ?? ""}
                  onChange={(e) =>
                    setSelection((prev) => ({ ...prev, [key]: e.target.value }))
                  }
                >
                  {values.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </SelectField>
              ))}
            </div>
          )}

          {!selectedVariant && (
            <Alert tone="warning">{t.unavailableVariant}</Alert>
          )}

          <div className={styles.quantityRow}>
            <TextField
              label={t.quantityLabel}
              type="number"
              min={1}
              max={selectedVariant?.quantity_available ?? 1}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value) || 1)}
            />
            <Button
              type="button"
              disabled={
                !selectedVariant ||
                stockStatus === "out_of_stock" ||
                addToCart.isPending
              }
              onClick={() => addToCart.mutate()}
            >
              {addToCart.isPending
                ? t.addingToCart
                : stockStatus === "out_of_stock"
                  ? t.outOfStockButton
                  : t.addToCartButton}
            </Button>
          </div>

          {addToCart.isSuccess && <Alert tone="success">{t.addedToCart}</Alert>}
          {addToCart.isError && (
            <Alert tone="danger">
              {addToCart.error instanceof ApiClientError
                ? addToCart.error.message
                : t.addToCartError}
            </Alert>
          )}

          {product.description && (
            <div className={styles.description}>
              <h2>{t.descriptionHeading}</h2>
              <p>{product.description}</p>
            </div>
          )}
        </div>
      </div>

      <RelatedProducts productId={product.id} heading={t.relatedHeading} />
    </div>
  );
}

function RelatedProducts({
  productId,
  heading,
}: {
  productId: string;
  heading: string;
}) {
  const { data: related } = useQuery({
    queryKey: ["related-products", productId],
    queryFn: () => getRelatedProducts(productId),
  });

  if (!related || related.length === 0) return null;

  return (
    <div className={styles.related}>
      <h2>{heading}</h2>
      <div className={styles.relatedGrid}>
        {related.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}

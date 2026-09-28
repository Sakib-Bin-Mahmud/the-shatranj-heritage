"use client";

import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listProducts } from "@/lib/api/catalog";
import styles from "./home.module.css";

// US-CAT / Phase F1: real featured products (`GET /products?featured=true`),
// not the static category cards the design canvas mocked up with —
// see docs/Frontend Implementation Plan.md Phase F1.
export function GrandCollection({
  eyebrow,
  title,
  emptyMessage,
  viewPieceLabel,
}: {
  eyebrow: string;
  title: string;
  emptyMessage: string;
  viewPieceLabel: string;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["products", { featured: true }],
    queryFn: () => listProducts({ featured: true, limit: 4 }),
  });

  const products = data?.items ?? [];

  return (
    <section className={styles.collection} id="grand-collection">
      <div className={styles.collectionHeading}>
        <span className={styles.eyebrow}>{eyebrow}</span>
        <h2 className={styles.collectionTitle}>{title}</h2>
      </div>

      {isLoading && (
        <span role="status" className="visually-hidden">
          Loading…
        </span>
      )}

      {!isLoading && products.length === 0 ? (
        <p className={styles.collectionEmpty}>{emptyMessage}</p>
      ) : (
        <div className={styles.collectionGrid}>
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className={styles.productCard} aria-hidden="true">
                  <div className={styles.productImageWrap} />
                </div>
              ))
            : products.map((product) => (
                <Link
                  key={product.id}
                  href={`/products/${product.slug}`}
                  className={styles.productCard}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div className={styles.productImageWrap}>
                    {product.primary_image_url ? (
                      <Image
                        src={product.primary_image_url}
                        alt=""
                        fill
                        sizes="(max-width: 640px) 50vw, 25vw"
                        className={styles.productImage}
                      />
                    ) : (
                      <span
                        className={styles.productImagePlaceholder}
                        aria-hidden="true"
                      >
                        ♞
                      </span>
                    )}
                  </div>
                  <span className={styles.productName}>{product.name}</span>
                  <p className={styles.productPrice}>৳{product.price}</p>
                  <span className={styles.productLink}>{viewPieceLabel}</span>
                </Link>
              ))}
        </div>
      )}
    </section>
  );
}

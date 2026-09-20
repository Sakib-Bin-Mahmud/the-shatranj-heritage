"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listProducts } from "@/lib/api/catalog";
import styles from "./home.module.css";

// US-CAT / Phase F1: real featured products (`GET /products?featured=true`),
// not the static category cards the design canvas mocked up with —
// see docs/Frontend Implementation Plan.md Phase F1.
export function GrandCollection() {
  const { data, isLoading } = useQuery({
    queryKey: ["products", { featured: true }],
    queryFn: () => listProducts({ featured: true, limit: 4 }),
  });

  const products = data?.items ?? [];

  return (
    <section className={styles.collection} id="grand-collection">
      <div className={styles.collectionHeading}>
        <span className={styles.eyebrow}>The Grand Collection</span>
        <h2 className={styles.collectionTitle}>Relics Fit for the Board</h2>
      </div>

      {!isLoading && products.length === 0 ? (
        <p className={styles.collectionEmpty}>
          New pieces are being catalogued — check back soon.
        </p>
      ) : (
        <div className={styles.collectionGrid}>
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className={styles.productCard}>
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
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={product.primary_image_url}
                        alt={product.name}
                        className={styles.productImage}
                      />
                    ) : (
                      <span className={styles.productImagePlaceholder}>♞</span>
                    )}
                  </div>
                  <span className={styles.productName}>{product.name}</span>
                  <p className={styles.productPrice}>৳{product.price}</p>
                  <span className={styles.productLink}>View piece →</span>
                </Link>
              ))}
        </div>
      )}
    </section>
  );
}

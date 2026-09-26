"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminArchiveProduct,
  adminGetProduct,
  adminUpdateProduct,
} from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Badge, Button, Skeleton } from "@/components/ui";
import { ProductForm, type ProductFormValues } from "../product-form";
import { VariantManager } from "./variant-manager";
import { ImageManager } from "./image-manager";
import styles from "../page.module.css";

export default function EditProductPage() {
  const { productId } = useParams<{ productId: string }>();
  const { accessToken } = useAdminAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const {
    data: product,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["admin-product", productId],
    queryFn: () => adminGetProduct(productId, accessToken),
  });

  const updateMutation = useMutation({
    mutationFn: (values: ProductFormValues) =>
      adminUpdateProduct(productId, values, accessToken),
    onSuccess: (updated) => {
      queryClient.setQueryData(["admin-product", productId], updated);
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    },
    onError: (err) => {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Could not save this product.",
      );
    },
  });

  const archiveMutation = useMutation({
    mutationFn: () => adminArchiveProduct(productId, accessToken),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      router.push("/admin/products");
    },
  });

  if (isLoading) {
    return (
      <div className={styles.page}>
        <Skeleton height="20rem" />
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className={styles.page}>
        <h1>Product not found</h1>
        <Link href="/admin/products">Back to products</Link>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link href="/admin/products" className={styles.backLink}>
        Back to products
      </Link>

      <div className={styles.headingRow}>
        <h1>{product.name}</h1>
        <Badge tone={product.status === "active" ? "success" : "danger"}>
          {product.status}
        </Badge>
      </div>

      <ProductForm
        initial={{
          sku: product.sku,
          name: product.name,
          slug: product.slug,
          description: product.description ?? "",
          category_id: product.category.id,
          artisan_id: product.artisan?.id ?? "",
          brand: product.brand ?? "",
          base_price: product.base_price,
          weight_grams: product.weight_grams,
          status: product.status as ProductFormValues["status"],
          is_featured: product.is_featured,
        }}
        submitLabel="Save changes"
        onSubmit={(values) => {
          setError(null);
          updateMutation.mutate(values);
        }}
        error={error}
        submitting={updateMutation.isPending}
      />

      <VariantManager product={product} />
      <ImageManager product={product} />

      {product.status !== "archived" && (
        <div className={styles.section}>
          <h2>Archive this product</h2>
          <p>
            Archiving hides it from the storefront. It stays intact for order
            history — nothing referencing it is deleted.
          </p>
          <Button
            variant="danger"
            onClick={() => archiveMutation.mutate()}
            disabled={archiveMutation.isPending}
          >
            Archive product
          </Button>
          {archiveMutation.isError && (
            <Alert tone="danger">Could not archive this product.</Alert>
          )}
        </div>
      )}
    </div>
  );
}

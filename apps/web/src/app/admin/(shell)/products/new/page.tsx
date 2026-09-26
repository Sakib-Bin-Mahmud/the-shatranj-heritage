"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminCreateProduct } from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import { ProductForm, type ProductFormValues } from "../product-form";
import styles from "../page.module.css";

export default function NewProductPage() {
  const { accessToken } = useAdminAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (values: ProductFormValues) =>
      adminCreateProduct(
        { ...values, base_price: values.base_price || "0" },
        accessToken,
      ),
    onSuccess: (product) => {
      router.push(`/admin/products/${product.id}`);
    },
    onError: (err) => {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Could not create this product.",
      );
    },
  });

  return (
    <div className={styles.page}>
      <Link href="/admin/products" className={styles.backLink}>
        Back to products
      </Link>
      <h1>New product</h1>
      <ProductForm
        submitLabel="Create product"
        onSubmit={(values) => {
          setError(null);
          createMutation.mutate(values);
        }}
        error={error}
        submitting={createMutation.isPending}
      />
    </div>
  );
}

"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminAddImage,
  adminDeleteImage,
  type ProductDetail,
} from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Badge, Button, CheckboxField } from "@/components/ui";
import styles from "../page.module.css";

export function ImageManager({ product }: { product: ProductDetail }) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isPrimary, setIsPrimary] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-product", product.id] });
  }

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      adminAddImage(product.id, { file, isPrimary }, accessToken),
    onSuccess: () => {
      invalidate();
      setIsPrimary(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    onError: (err) => {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Could not upload this image.",
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (imageId: string) =>
      adminDeleteImage(product.id, imageId, accessToken),
    onSuccess: () => invalidate(),
  });

  return (
    <div className={styles.section}>
      <h2>Images</h2>

      <div className={styles.imageGrid}>
        {product.images.map((image) => (
          <div key={image.id} className={styles.imageCard}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={image.url} alt={image.alt_text ?? ""} />
            {image.is_primary && (
              <Badge tone="info" className={styles.imageBadge}>
                Primary
              </Badge>
            )}
            <Button
              variant="danger"
              size="sm"
              onClick={() => deleteMutation.mutate(image.id)}
              disabled={deleteMutation.isPending}
            >
              Delete
            </Button>
          </div>
        ))}
      </div>

      {error && <Alert tone="danger">{error}</Alert>}

      <div className={styles.uploadRow}>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setError(null);
            uploadMutation.mutate(file);
          }}
        />
        <CheckboxField
          label="Set as primary"
          checked={isPrimary}
          onChange={(e) => setIsPrimary(e.target.checked)}
        />
        {uploadMutation.isPending && <span>Uploading…</span>}
      </div>
    </div>
  );
}

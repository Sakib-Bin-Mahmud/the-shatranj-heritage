"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminListArtisans, adminListCategories } from "@/lib/api/catalog";
import { slugify } from "@/lib/slugify";
import {
  Alert,
  Button,
  CheckboxField,
  SelectField,
  TextField,
} from "@/components/ui";
import type { ProductInput } from "@/lib/api/catalog";
import styles from "./page.module.css";

export type ProductFormValues = ProductInput;

const EMPTY_VALUES: ProductFormValues = {
  sku: "",
  name: "",
  slug: "",
  description: "",
  category_id: "",
  artisan_id: "",
  brand: "",
  base_price: "",
  weight_grams: undefined,
  status: "draft",
  meta_title: "",
  meta_description: "",
  is_featured: false,
};

export function ProductForm({
  initial,
  submitLabel,
  onSubmit,
  error,
  submitting,
}: {
  initial?: Partial<ProductFormValues>;
  submitLabel: string;
  onSubmit: (values: ProductFormValues) => void;
  error?: string | null;
  submitting?: boolean;
}) {
  const { accessToken } = useAdminAuth();
  const [values, setValues] = useState<ProductFormValues>({
    ...EMPTY_VALUES,
    ...initial,
  });
  const [slugTouched, setSlugTouched] = useState(Boolean(initial?.slug));

  const { data: categories } = useQuery({
    queryKey: ["admin-categories-flat"],
    queryFn: () => adminListCategories(accessToken),
  });
  const { data: artisans } = useQuery({
    queryKey: ["admin-artisans"],
    queryFn: () => adminListArtisans(accessToken),
  });

  function set<K extends keyof ProductFormValues>(
    key: K,
    value: ProductFormValues[K],
  ) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function handleNameChange(name: string) {
    set("name", name);
    if (!slugTouched) set("slug", slugify(name));
  }

  return (
    <form
      className={styles.productForm}
      onSubmit={(e) => {
        e.preventDefault();
        // artisan_id is a UUID field server-side (`uuid.UUID | None`) —
        // "" is a valid string value for the <select> (matching the
        // "None" option), but not a valid UUID, so it must be
        // normalized here rather than left for the select's own
        // onChange, which never fires if the field is left untouched.
        onSubmit({ ...values, artisan_id: values.artisan_id || null });
      }}
    >
      <div className={styles.formGrid}>
        <TextField
          label="Name"
          required
          value={values.name}
          onChange={(e) => handleNameChange(e.target.value)}
        />
        <TextField
          label="Slug"
          required
          value={values.slug}
          onChange={(e) => {
            setSlugTouched(true);
            set("slug", e.target.value);
          }}
        />
        <TextField
          label="SKU"
          required
          value={values.sku}
          onChange={(e) => set("sku", e.target.value)}
        />
        <TextField
          label="Brand"
          value={values.brand ?? ""}
          onChange={(e) => set("brand", e.target.value)}
        />
        <SelectField
          label="Category"
          required
          value={values.category_id}
          onChange={(e) => set("category_id", e.target.value)}
        >
          <option value="" disabled>
            Select a category…
          </option>
          {categories?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Artisan"
          value={values.artisan_id ?? ""}
          onChange={(e) => set("artisan_id", e.target.value || null)}
        >
          <option value="">None</option>
          {artisans?.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </SelectField>
        <TextField
          label="Base price (৳)"
          required
          inputMode="decimal"
          value={values.base_price}
          onChange={(e) => set("base_price", e.target.value)}
        />
        <TextField
          label="Weight (grams)"
          type="number"
          value={values.weight_grams ?? ""}
          onChange={(e) =>
            set(
              "weight_grams",
              e.target.value === "" ? null : Number(e.target.value),
            )
          }
        />
        <SelectField
          label="Status"
          value={values.status}
          onChange={(e) =>
            set("status", e.target.value as ProductFormValues["status"])
          }
        >
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </SelectField>
      </div>

      <TextField
        label="Description"
        value={values.description ?? ""}
        onChange={(e) => set("description", e.target.value)}
      />

      <div className={styles.formGrid}>
        <TextField
          label="Meta title"
          value={values.meta_title ?? ""}
          onChange={(e) => set("meta_title", e.target.value)}
        />
        <TextField
          label="Meta description"
          value={values.meta_description ?? ""}
          onChange={(e) => set("meta_description", e.target.value)}
        />
      </div>

      <CheckboxField
        label="Featured on homepage"
        checked={values.is_featured ?? false}
        onChange={(e) => set("is_featured", e.target.checked)}
      />

      {error && <Alert tone="danger">{error}</Alert>}

      <div className={styles.modalActions}>
        <Button type="submit" disabled={submitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}

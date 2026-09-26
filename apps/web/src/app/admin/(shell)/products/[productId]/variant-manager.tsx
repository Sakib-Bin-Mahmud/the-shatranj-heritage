"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminArchiveVariant,
  adminCreateVariant,
  adminUpdateVariant,
  type ProductDetail,
  type ProductVariant,
  type VariantInput,
} from "@/lib/api/catalog";
import { ApiClientError } from "@/lib/api-client";
import {
  Alert,
  Badge,
  Button,
  CheckboxField,
  Modal,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";
import styles from "../page.module.css";

const EMPTY_INPUT: VariantInput = {
  sku: "",
  variant_name: "",
  price_override: "",
  weight_grams: undefined,
  is_default: false,
};

export function VariantManager({ product }: { product: ProductDetail }) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<ProductVariant | null>(null);
  const [form, setForm] = useState<VariantInput>(EMPTY_INPUT);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-product", product.id] });
  }

  function openCreate() {
    setForm(EMPTY_INPUT);
    setCreating(true);
  }

  function openEdit(variant: ProductVariant) {
    setForm({
      sku: variant.sku,
      variant_name: variant.variant_name,
      price_override: variant.price_override ?? "",
      weight_grams: variant.weight_grams,
      is_default: variant.is_default,
    });
    setEditing(variant);
  }

  function close() {
    setCreating(false);
    setEditing(null);
  }

  const saveMutation = useMutation({
    mutationFn: () => {
      const input = {
        variant_name: form.variant_name,
        price_override: form.price_override || null,
        weight_grams: form.weight_grams ?? null,
        is_default: form.is_default,
      };
      return editing
        ? adminUpdateVariant(product.id, editing.id, input, accessToken)
        : adminCreateVariant(
            product.id,
            { ...input, sku: form.sku },
            accessToken,
          );
    },
    onSuccess: () => {
      invalidate();
      close();
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (variantId: string) =>
      adminArchiveVariant(product.id, variantId, accessToken),
    onSuccess: () => invalidate(),
  });

  const columns: TableColumn<ProductVariant>[] = [
    { key: "sku", header: "SKU", render: (v) => v.sku },
    {
      key: "variant_name",
      header: "Name",
      render: (v) => (
        <>
          {v.variant_name} {v.is_default && <Badge tone="info">Default</Badge>}
        </>
      ),
    },
    {
      key: "effective_price",
      header: "Price",
      render: (v) => `৳${v.effective_price}`,
    },
    {
      key: "quantity_available",
      header: "Available",
      render: (v) => v.quantity_available,
    },
    {
      key: "status",
      header: "Status",
      render: (v) => (
        <Badge tone={v.status === "active" ? "success" : "danger"}>
          {v.status}
        </Badge>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (v) => (
        <div className={styles.rowActions}>
          <Button variant="secondary" size="sm" onClick={() => openEdit(v)}>
            Edit
          </Button>
          {v.status === "active" && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => archiveMutation.mutate(v.id)}
              disabled={archiveMutation.isPending}
            >
              Archive
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className={styles.section}>
      <div className={styles.headingRow}>
        <h2>Variants</h2>
        <Button onClick={openCreate}>Add variant</Button>
      </div>

      <Table
        columns={columns}
        rows={product.variants}
        rowKey={(v) => v.id}
        emptyTitle="No variants yet — add one to let customers buy this product"
      />

      <Modal
        open={creating || Boolean(editing)}
        onClose={close}
        title={editing ? "Edit variant" : "Add variant"}
      >
        <form
          className={styles.modalForm}
          onSubmit={(e) => {
            e.preventDefault();
            saveMutation.mutate();
          }}
        >
          {!editing && (
            <TextField
              label="SKU"
              required
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
            />
          )}
          <TextField
            label="Variant name"
            required
            value={form.variant_name}
            onChange={(e) => setForm({ ...form, variant_name: e.target.value })}
          />
          <TextField
            label="Price override (৳, optional)"
            inputMode="decimal"
            value={form.price_override ?? ""}
            onChange={(e) =>
              setForm({ ...form, price_override: e.target.value })
            }
            hint="Leave blank to use the product's base price."
          />
          <TextField
            label="Weight (grams, optional)"
            type="number"
            value={form.weight_grams ?? ""}
            onChange={(e) =>
              setForm({
                ...form,
                weight_grams:
                  e.target.value === "" ? undefined : Number(e.target.value),
              })
            }
          />
          <CheckboxField
            label="Default variant"
            checked={form.is_default ?? false}
            onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
          />
          {saveMutation.isError && (
            <Alert tone="danger">
              {saveMutation.error instanceof ApiClientError
                ? saveMutation.error.message
                : "Could not save this variant."}
            </Alert>
          )}
          <div className={styles.modalActions}>
            <Button type="button" variant="ghost" onClick={close}>
              Cancel
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              Save
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

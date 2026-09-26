"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { listInventory, type InventoryItem } from "@/lib/api/inventory";
import {
  Badge,
  Button,
  CheckboxField,
  Table,
  type TableColumn,
} from "@/components/ui";
import { AdjustModal } from "./adjust-modal";
import styles from "./page.module.css";

const PAGE_SIZE = 20;

export default function AdminInventoryPage() {
  const { accessToken, hasPermission } = useAdminAuth();
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [adjusting, setAdjusting] = useState<InventoryItem | null>(null);
  const canAdjust = hasPermission("inventory.write");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-inventory", lowStockOnly, page],
    queryFn: () =>
      listInventory(
        { low_stock: lowStockOnly, page, limit: PAGE_SIZE },
        accessToken,
      ),
  });

  const columns: TableColumn<InventoryItem>[] = [
    { key: "product_name", header: "Product", render: (i) => i.product_name },
    { key: "variant_name", header: "Variant", render: (i) => i.variant_name },
    { key: "variant_sku", header: "SKU", render: (i) => i.variant_sku },
    {
      key: "quantity_on_hand",
      header: "On hand",
      render: (i) => i.quantity_on_hand,
    },
    {
      key: "quantity_reserved",
      header: "Reserved",
      render: (i) => i.quantity_reserved,
    },
    {
      key: "quantity_available",
      header: "Available",
      render: (i) => i.quantity_available,
    },
    {
      key: "reorder_threshold",
      header: "Reorder at",
      render: (i) => i.reorder_threshold,
    },
    {
      key: "is_low_stock",
      header: "Status",
      render: (i) =>
        i.is_low_stock ? (
          <Badge tone="warning">Low stock</Badge>
        ) : (
          <Badge tone="success">OK</Badge>
        ),
    },
    ...(canAdjust
      ? [
          {
            key: "actions",
            header: "",
            render: (i: InventoryItem) => (
              <Button size="sm" onClick={() => setAdjusting(i)}>
                Adjust
              </Button>
            ),
          } satisfies TableColumn<InventoryItem>,
        ]
      : []),
  ];

  return (
    <div className={styles.page}>
      <h1>Inventory</h1>

      <CheckboxField
        label="Low stock only"
        checked={lowStockOnly}
        onChange={(e) => {
          setLowStockOnly(e.target.checked);
          setPage(1);
        }}
      />

      <Table
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(i) => i.id}
        isLoading={isLoading}
        emptyTitle="Nothing to show"
        pagination={
          data?.meta
            ? {
                page: data.meta.page,
                totalPages: data.meta.total_pages,
                onPageChange: setPage,
              }
            : undefined
        }
      />

      {adjusting && (
        <AdjustModal item={adjusting} onClose={() => setAdjusting(null)} />
      )}
    </div>
  );
}

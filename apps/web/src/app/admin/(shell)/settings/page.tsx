"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminListShippingRates, type ShippingRate } from "@/lib/api/settings";
import { titleCase } from "@/lib/text-format";
import { Badge, Button, Table, type TableColumn } from "@/components/ui";
import { EditRateModal } from "./edit-rate-modal";
import styles from "./page.module.css";

export default function AdminSettingsPage() {
  const { accessToken } = useAdminAuth();
  const [editing, setEditing] = useState<ShippingRate | null>(null);

  const { data: rates, isLoading } = useQuery({
    queryKey: ["admin-shipping-rates"],
    queryFn: () => adminListShippingRates(accessToken),
  });

  const columns: TableColumn<ShippingRate>[] = [
    { key: "zone", header: "Zone", render: (r) => titleCase(r.zone) },
    { key: "method", header: "Method", render: (r) => titleCase(r.method) },
    { key: "base_rate", header: "Base rate", render: (r) => `৳${r.base_rate}` },
    {
      key: "base_weight_grams",
      header: "Base weight",
      render: (r) => `${r.base_weight_grams} g`,
    },
    {
      key: "per_kg_rate",
      header: "Per-kg rate",
      render: (r) => `৳${r.per_kg_rate}`,
    },
    {
      key: "is_active",
      header: "Status",
      render: (r) => (
        <Badge tone={r.is_active ? "success" : "neutral"}>
          {r.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <Button variant="secondary" onClick={() => setEditing(r)}>
          Edit
        </Button>
      ),
    },
  ];

  return (
    <div className={styles.page}>
      <h1>Settings</h1>
      <p>Shipping rates used to calculate checkout shipping costs by zone.</p>

      <Table
        columns={columns}
        rows={rates ?? []}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        emptyTitle="No shipping rates configured"
      />

      <EditRateModal rate={editing} onClose={() => setEditing(null)} />
    </div>
  );
}

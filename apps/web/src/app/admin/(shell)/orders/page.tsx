"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminListOrders, type OrderSummary } from "@/lib/api/orders";
import { orderStatusTone } from "@/lib/order-status";
import { titleCase } from "@/lib/text-format";
import { Badge, SelectField, Table, type TableColumn } from "@/components/ui";
import styles from "./page.module.css";

const PAGE_SIZE = 20;
const STATUSES = [
  "pending",
  "awaiting_payment",
  "confirmed",
  "packed",
  "shipped",
  "delivered",
  "cancelled",
  "returned",
  "refunded",
];

export default function AdminOrdersPage() {
  const { accessToken } = useAdminAuth();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders", status, page],
    queryFn: () =>
      adminListOrders(
        { status: status || undefined, page, limit: PAGE_SIZE },
        accessToken,
      ),
  });

  const columns: TableColumn<OrderSummary>[] = [
    {
      key: "order_number",
      header: "Order",
      render: (o) => (
        <Link href={`/admin/orders/${o.id}`}>{o.order_number}</Link>
      ),
    },
    {
      key: "placed_at",
      header: "Placed",
      render: (o) => new Date(o.placed_at).toLocaleString(),
    },
    {
      key: "status",
      header: "Status",
      render: (o) => (
        <Badge tone={orderStatusTone(o.status)}>{titleCase(o.status)}</Badge>
      ),
    },
    {
      key: "total_amount",
      header: "Total",
      render: (o) => `৳${o.total_amount}`,
    },
  ];

  return (
    <div className={styles.page}>
      <h1>Orders</h1>

      <SelectField
        label="Status"
        value={status}
        onChange={(e) => {
          setStatus(e.target.value);
          setPage(1);
        }}
        className={styles.statusFilter}
      >
        <option value="">All</option>
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {titleCase(s)}
          </option>
        ))}
      </SelectField>

      <Table
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(o) => o.id}
        isLoading={isLoading}
        emptyTitle="No orders yet"
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
    </div>
  );
}

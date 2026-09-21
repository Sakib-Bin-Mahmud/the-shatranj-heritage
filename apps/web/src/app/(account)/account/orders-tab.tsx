"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { listMyOrders, type OrderSummary } from "@/lib/api/orders";
import { orderStatusLabel, orderStatusTone } from "@/lib/order-status";
import {
  Badge,
  Button,
  EmptyState,
  Table,
  type TableColumn,
} from "@/components/ui";
import styles from "./page.module.css";

const PAGE_SIZE = 10;

export function OrdersTab({ accessToken }: { accessToken: string | null }) {
  const { dict } = useDictionary();
  const t = dict.account.orders;
  const router = useRouter();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["my-orders", page],
    queryFn: () => listMyOrders({ page, limit: PAGE_SIZE }, accessToken),
    enabled: Boolean(accessToken),
  });

  const columns: TableColumn<OrderSummary>[] = [
    {
      key: "order_number",
      header: t.columnOrder,
      render: (order) => (
        <Link href={`/account/orders/${order.order_number}`}>
          {order.order_number}
        </Link>
      ),
    },
    {
      key: "placed_at",
      header: t.columnDate,
      render: (order) => new Date(order.placed_at).toLocaleDateString(),
    },
    {
      key: "status",
      header: t.columnStatus,
      render: (order) => (
        <Badge tone={orderStatusTone(order.status)}>
          {orderStatusLabel(dict, order.status)}
        </Badge>
      ),
    },
    {
      key: "total_amount",
      header: t.columnTotal,
      render: (order) => `৳${order.total_amount}`,
    },
    {
      key: "actions",
      header: "",
      render: (order) => (
        <Link href={`/account/orders/${order.order_number}`}>
          <Button variant="secondary" size="sm">
            {t.viewButton}
          </Button>
        </Link>
      ),
    },
  ];

  if (isError) {
    return (
      <div className={styles.section}>
        <h2>{t.heading}</h2>
        <EmptyState title={t.loadError} />
      </div>
    );
  }

  const meta = data?.meta;

  if (!isLoading && data && data.items.length === 0) {
    return (
      <div className={styles.section}>
        <h2>{t.heading}</h2>
        <EmptyState
          title={t.emptyHeading}
          action={
            <Button onClick={() => router.push("/products")}>
              {t.emptyAction}
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className={styles.section}>
      <h2>{t.heading}</h2>
      <Table
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(order) => order.id}
        isLoading={isLoading}
        emptyTitle={t.emptyHeading}
        pagination={
          meta
            ? {
                page: meta.page,
                totalPages: meta.total_pages,
                onPageChange: setPage,
              }
            : undefined
        }
      />
    </div>
  );
}

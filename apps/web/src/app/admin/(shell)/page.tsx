"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { getInventoryReport, getSalesReport } from "@/lib/api/reports";
import { accessibleLinks } from "@/components/admin-sidebar-nav";
import { titleCase, titleCaseList } from "@/lib/text-format";
import {
  Alert,
  Badge,
  Card,
  Skeleton,
  Table,
  type TableColumn,
} from "@/components/ui";
import type { LowStockItem, SlowMovingItem } from "@/lib/api/reports";
import styles from "./page.module.css";

const DASHBOARD_ROW_LIMIT = 5;

const lowStockColumns: TableColumn<LowStockItem>[] = [
  { key: "product_name", header: "Product", render: (r) => r.product_name },
  { key: "sku", header: "SKU", render: (r) => r.sku },
  {
    key: "quantity_available",
    header: "Available",
    render: (r) => r.quantity_available,
  },
  {
    key: "reorder_threshold",
    header: "Reorder at",
    render: (r) => r.reorder_threshold,
  },
];

const slowMovingColumns: TableColumn<SlowMovingItem>[] = [
  { key: "product_name", header: "Product", render: (r) => r.product_name },
  { key: "sku", header: "SKU", render: (r) => r.sku },
  {
    key: "quantity_on_hand",
    header: "On hand",
    render: (r) => r.quantity_on_hand,
  },
  {
    key: "days_since_last_sale",
    header: "Days since last sale",
    render: (r) => r.days_since_last_sale ?? "Never sold",
  },
];

export default function AdminDashboardPage() {
  const { admin, accessToken, hasPermission } = useAdminAuth();
  const canSeeReports = hasPermission("reports.read");

  const { data: sales, isLoading: salesLoading } = useQuery({
    queryKey: ["admin-dashboard-sales"],
    queryFn: () => getSalesReport({}, accessToken),
    enabled: canSeeReports,
  });

  const { data: inventory, isLoading: inventoryLoading } = useQuery({
    queryKey: ["admin-dashboard-inventory"],
    queryFn: () => getInventoryReport({}, accessToken),
    enabled: canSeeReports,
  });

  if (!canSeeReports) {
    const links = accessibleLinks(hasPermission);
    return (
      <div className={styles.page}>
        <h1>Welcome, {admin?.full_name}</h1>
        <p className={styles.subtitle}>
          Role{admin && admin.roles.length > 1 ? "s" : ""}:{" "}
          {admin && admin.roles.length > 0
            ? titleCaseList(admin.roles)
            : "none assigned"}
        </p>
        {links.length > 0 ? (
          <Card title="Your sections">
            <ul className={styles.linkList}>
              {links.map((link) => (
                <li key={link.href}>
                  <Link href={link.href}>{link.label}</Link>
                </li>
              ))}
            </ul>
          </Card>
        ) : (
          <Alert tone="info">
            Your account has no permissions assigned yet. Ask a super admin to
            grant you a role.
          </Alert>
        )}
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1>Dashboard</h1>

      {salesLoading ? (
        <Skeleton height="8rem" />
      ) : sales ? (
        <div className={styles.statGrid}>
          <Card title="Total orders">
            <span className={styles.statValue}>{sales.total_orders}</span>
          </Card>
          <Card title="Total revenue">
            <span className={styles.statValue}>৳{sales.total_revenue}</span>
          </Card>
          <Card title="Average order value">
            <span className={styles.statValue}>
              ৳{sales.average_order_value}
            </span>
          </Card>
        </div>
      ) : null}

      {sales && (
        <Card title="Orders by status">
          <div className={styles.statusRow}>
            {Object.entries(sales.orders_by_status).map(([status, count]) => (
              <Badge key={status} tone="neutral">
                {titleCase(status)}: {count}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {inventoryLoading ? (
        <Skeleton height="12rem" />
      ) : inventory ? (
        <>
          <Card
            title={`Low stock${inventory.low_stock.length > DASHBOARD_ROW_LIMIT ? ` (${inventory.low_stock.length} total)` : ""}`}
          >
            <Table
              columns={lowStockColumns}
              rows={inventory.low_stock.slice(0, DASHBOARD_ROW_LIMIT)}
              rowKey={(r) => r.product_variant_id}
              emptyTitle="Nothing is low on stock"
            />
          </Card>

          <Card
            title={`Slow moving${inventory.slow_moving.length > DASHBOARD_ROW_LIMIT ? ` (${inventory.slow_moving.length} total)` : ""}`}
          >
            <Table
              columns={slowMovingColumns}
              rows={inventory.slow_moving.slice(0, DASHBOARD_ROW_LIMIT)}
              rowKey={(r) => r.product_variant_id}
              emptyTitle="Nothing is moving slowly"
            />
          </Card>
        </>
      ) : null}
    </div>
  );
}

"use client";

import { usePageTitle } from "@/lib/use-page-title";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  getCustomerReport,
  getInventoryReport,
  getRefundReport,
  getRevenueReport,
  getSalesReport,
  getTopSellingProducts,
  type LowStockItem,
  type SlowMovingItem,
  type TopSellingProduct,
} from "@/lib/api/reports";
import { titleCase } from "@/lib/text-format";
import { formatAmount, formatInt } from "@/lib/format-number";
import {
  Alert,
  Card,
  SelectField,
  Skeleton,
  Table,
  TextField,
  type TableColumn,
} from "@/components/ui";
import { DateRangeFilter, type DateRange } from "./date-range-filter";
import { TimeSeriesChart } from "./time-series-chart";
import { ValueBarList } from "./value-bar-list";
import { Meter } from "./meter";
import styles from "./page.module.css";

type Tab =
  "sales" | "revenue" | "customers" | "inventory" | "products" | "refunds";
type GroupBy = "day" | "week" | "month";

const TABS: { id: Tab; label: string }[] = [
  { id: "sales", label: "Sales" },
  { id: "revenue", label: "Revenue" },
  { id: "customers", label: "Customers" },
  { id: "inventory", label: "Inventory" },
  { id: "products", label: "Top Products" },
  { id: "refunds", label: "Refunds" },
];

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function defaultRange(): DateRange {
  const to = new Date();
  const from = new Date();
  from.setUTCDate(from.getUTCDate() - 30);
  return { fromDate: isoDate(from), toDate: isoDate(to) };
}

const lowStockColumns: TableColumn<LowStockItem>[] = [
  { key: "product_name", header: "Product", render: (r) => r.product_name },
  { key: "variant_name", header: "Variant", render: (r) => r.variant_name },
  { key: "sku", header: "SKU", render: (r) => r.sku },
  {
    key: "quantity_available",
    header: "Available",
    render: (r) => formatInt(r.quantity_available),
  },
  {
    key: "reorder_threshold",
    header: "Reorder at",
    render: (r) => formatInt(r.reorder_threshold),
  },
];

const slowMovingColumns: TableColumn<SlowMovingItem>[] = [
  { key: "product_name", header: "Product", render: (r) => r.product_name },
  { key: "variant_name", header: "Variant", render: (r) => r.variant_name },
  { key: "sku", header: "SKU", render: (r) => r.sku },
  {
    key: "quantity_on_hand",
    header: "On hand",
    render: (r) => formatInt(r.quantity_on_hand),
  },
  {
    key: "days_since_last_sale",
    header: "Days since last sale",
    render: (r) =>
      r.days_since_last_sale === null
        ? "Never sold"
        : formatInt(r.days_since_last_sale),
  },
];

const topProductColumns: TableColumn<TopSellingProduct>[] = [
  { key: "product_name", header: "Product", render: (r) => r.product_name },
  { key: "sku", header: "SKU", render: (r) => r.sku },
  {
    key: "quantity_sold",
    header: "Units sold",
    render: (r) => formatInt(r.quantity_sold),
  },
  {
    key: "revenue",
    header: "Revenue",
    render: (r) => `৳${formatAmount(r.revenue)}`,
  },
];

export default function AdminReportsPage() {
  usePageTitle("Reports");
  const { accessToken } = useAdminAuth();
  const [tab, setTab] = useState<Tab>("sales");
  const [range, setRange] = useState<DateRange>(defaultRange);
  const [revenueGroupBy, setRevenueGroupBy] = useState<GroupBy>("day");
  const [customerGroupBy, setCustomerGroupBy] = useState<GroupBy>("day");
  const [slowMovingDays, setSlowMovingDays] = useState(30);
  const [topLimit, setTopLimit] = useState(10);

  const dateParams = { from_date: range.fromDate, to_date: range.toDate };

  const sales = useQuery({
    queryKey: ["admin-report-sales", range],
    queryFn: () => getSalesReport(dateParams, accessToken),
    enabled: tab === "sales",
  });

  const revenue = useQuery({
    queryKey: ["admin-report-revenue", range, revenueGroupBy],
    queryFn: () =>
      getRevenueReport(
        { ...dateParams, group_by: revenueGroupBy },
        accessToken,
      ),
    enabled: tab === "revenue",
  });

  const customers = useQuery({
    queryKey: ["admin-report-customers", range, customerGroupBy],
    queryFn: () =>
      getCustomerReport(
        { ...dateParams, group_by: customerGroupBy },
        accessToken,
      ),
    enabled: tab === "customers",
  });

  const inventory = useQuery({
    queryKey: ["admin-report-inventory", slowMovingDays],
    queryFn: () =>
      getInventoryReport({ slow_moving_days: slowMovingDays }, accessToken),
    enabled: tab === "inventory",
  });

  const products = useQuery({
    queryKey: ["admin-report-products", range, topLimit],
    queryFn: () =>
      getTopSellingProducts({ ...dateParams, limit: topLimit }, accessToken),
    enabled: tab === "products",
  });

  const refunds = useQuery({
    queryKey: ["admin-report-refunds", range],
    queryFn: () => getRefundReport(dateParams, accessToken),
    enabled: tab === "refunds",
  });

  const usesDateRange = tab !== "inventory";

  return (
    <div className={styles.page}>
      <h1>Reports</h1>

      <div className={styles.tabs} role="tablist" aria-label="Report sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={tab === t.id}
            className={`${styles.tab} ${tab === t.id ? styles.tabActive : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {usesDateRange && <DateRangeFilter range={range} onChange={setRange} />}

      {tab === "sales" && (
        <div className={styles.section}>
          {sales.isLoading && <Skeleton height="10rem" />}
          {sales.isError && (
            <Alert tone="danger">Could not load the sales report.</Alert>
          )}
          {sales.data && (
            <>
              <div className={styles.statGrid}>
                <Card title="Total orders" headingLevel="h2">
                  <span className={styles.statValue}>
                    {formatInt(sales.data.total_orders)}
                  </span>
                </Card>
                <Card title="Total revenue" headingLevel="h2">
                  <span className={styles.statValue}>
                    ৳{formatAmount(sales.data.total_revenue)}
                  </span>
                </Card>
                <Card title="Average order value" headingLevel="h2">
                  <span className={styles.statValue}>
                    ৳{formatAmount(sales.data.average_order_value)}
                  </span>
                </Card>
              </div>
              <Card title="Orders by status" headingLevel="h2">
                <ValueBarList
                  items={Object.entries(sales.data.orders_by_status).map(
                    ([status, count]) => ({
                      key: status,
                      label: titleCase(status),
                      value: count,
                      displayValue: formatInt(count),
                    }),
                  )}
                />
              </Card>
            </>
          )}
        </div>
      )}

      {tab === "revenue" && (
        <div className={styles.section}>
          <SelectField
            label="Group by"
            value={revenueGroupBy}
            onChange={(e) => setRevenueGroupBy(e.target.value as GroupBy)}
          >
            <option value="day">Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </SelectField>
          <Card title="Revenue over time" headingLevel="h2">
            {revenue.isLoading && <Skeleton height="16rem" />}
            {revenue.isError && (
              <Alert tone="danger">Could not load the revenue report.</Alert>
            )}
            {revenue.data && (
              <TimeSeriesChart
                data={revenue.data.points.map((p) => ({
                  period: p.period,
                  value: Number(p.revenue),
                }))}
                seriesLabel="Revenue"
                valueFormatter={(v) => `৳${formatAmount(String(v))}`}
              />
            )}
          </Card>
        </div>
      )}

      {tab === "customers" && (
        <div className={styles.section}>
          {customers.isLoading && <Skeleton height="10rem" />}
          {customers.isError && (
            <Alert tone="danger">Could not load the customer report.</Alert>
          )}
          {customers.data && (
            <>
              <div className={styles.statGrid}>
                <Card title="Total customers" headingLevel="h2">
                  <span className={styles.statValue}>
                    {formatInt(customers.data.total_customers)}
                  </span>
                </Card>
                <Card title="New customers in range" headingLevel="h2">
                  <span className={styles.statValue}>
                    {formatInt(customers.data.new_customers)}
                  </span>
                </Card>
                <Card title="Repeat-customer rate" headingLevel="h2">
                  <Meter
                    label="Repeat customers"
                    percent={customers.data.repeat_customer_rate}
                  />
                </Card>
              </div>
              <SelectField
                label="Group by"
                value={customerGroupBy}
                onChange={(e) => setCustomerGroupBy(e.target.value as GroupBy)}
              >
                <option value="day">Day</option>
                <option value="week">Week</option>
                <option value="month">Month</option>
              </SelectField>
              <Card title="Customer growth" headingLevel="h2">
                <TimeSeriesChart
                  data={customers.data.growth.map((p) => ({
                    period: p.period,
                    value: p.new_customers,
                  }))}
                  seriesLabel="New customers"
                  valueFormatter={(v) => formatInt(v)}
                />
              </Card>
            </>
          )}
        </div>
      )}

      {tab === "inventory" && (
        <div className={styles.section}>
          <TextField
            label="Slow-moving threshold (days)"
            type="number"
            min={1}
            max={365}
            value={slowMovingDays}
            onChange={(e) => setSlowMovingDays(Number(e.target.value) || 30)}
          />
          {inventory.isLoading && <Skeleton height="16rem" />}
          {inventory.isError && (
            <Alert tone="danger">Could not load the inventory report.</Alert>
          )}
          {inventory.data && (
            <>
              <Card
                title={`Low stock (${inventory.data.low_stock.length})`}
                headingLevel="h2"
              >
                <Table
                  columns={lowStockColumns}
                  rows={inventory.data.low_stock}
                  rowKey={(r) => r.product_variant_id}
                  emptyTitle="Nothing is low on stock"
                />
              </Card>
              <Card
                title={`Slow moving (${inventory.data.slow_moving.length})`}
                headingLevel="h2"
              >
                <Table
                  columns={slowMovingColumns}
                  rows={inventory.data.slow_moving}
                  rowKey={(r) => r.product_variant_id}
                  emptyTitle="Nothing is moving slowly"
                />
              </Card>
            </>
          )}
        </div>
      )}

      {tab === "products" && (
        <div className={styles.section}>
          <TextField
            label="Show top"
            type="number"
            min={1}
            max={100}
            value={topLimit}
            onChange={(e) => setTopLimit(Number(e.target.value) || 10)}
          />
          {products.isLoading && <Skeleton height="12rem" />}
          {products.isError && (
            <Alert tone="danger">
              Could not load the top-selling products report.
            </Alert>
          )}
          {products.data && (
            <Table
              columns={topProductColumns}
              rows={products.data.items}
              rowKey={(r) => r.product_variant_id}
              emptyTitle="No products sold in this range"
            />
          )}
        </div>
      )}

      {tab === "refunds" && (
        <div className={styles.section}>
          {refunds.isLoading && <Skeleton height="10rem" />}
          {refunds.isError && (
            <Alert tone="danger">Could not load the refund report.</Alert>
          )}
          {refunds.data && (
            <>
              <div className={styles.statGrid}>
                <Card title="Total refunds" headingLevel="h2">
                  <span className={styles.statValue}>
                    {formatInt(refunds.data.total_refunds)}
                  </span>
                </Card>
                <Card title="Total refund amount" headingLevel="h2">
                  <span className={styles.statValue}>
                    ৳{formatAmount(refunds.data.total_refund_amount)}
                  </span>
                </Card>
              </div>
              <Card title="Refunds by status" headingLevel="h2">
                <Table
                  columns={[
                    {
                      key: "status",
                      header: "Status",
                      render: (r) => titleCase(r.status),
                    },
                    {
                      key: "count",
                      header: "Count",
                      render: (r) => formatInt(r.count),
                    },
                    {
                      key: "amount",
                      header: "Amount",
                      render: (r) => `৳${formatAmount(r.amount)}`,
                    },
                  ]}
                  rows={refunds.data.by_status}
                  rowKey={(r) => r.status}
                  emptyTitle="No refunds in this range"
                />
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}

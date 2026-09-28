import { apiFetch } from "@/lib/api-client";

export type DateRangeParams = { from_date?: string; to_date?: string };

export type SalesReport = {
  from_date: string;
  to_date: string;
  total_orders: number;
  total_revenue: string;
  average_order_value: string;
  orders_by_status: Record<string, number>;
};

export type RevenuePoint = {
  period: string;
  revenue: string;
  order_count: number;
};

export type RevenueReport = {
  from_date: string;
  to_date: string;
  group_by: string;
  points: RevenuePoint[];
};

export type LowStockItem = {
  product_variant_id: string;
  sku: string;
  variant_name: string;
  product_name: string;
  quantity_on_hand: number;
  quantity_available: number;
  reorder_threshold: number;
};

export type SlowMovingItem = {
  product_variant_id: string;
  sku: string;
  variant_name: string;
  product_name: string;
  quantity_on_hand: number;
  days_since_last_sale: number | null;
};

export type InventoryReport = {
  low_stock: LowStockItem[];
  slow_moving: SlowMovingItem[];
};

export type CustomerGrowthPoint = { period: string; new_customers: number };

export type CustomerReport = {
  from_date: string;
  to_date: string;
  group_by: string;
  total_customers: number;
  new_customers: number;
  repeat_customer_rate: number;
  growth: CustomerGrowthPoint[];
};

export type TopSellingProduct = {
  product_variant_id: string;
  sku: string;
  product_name: string;
  quantity_sold: number;
  revenue: string;
};

export type TopSellingProductsReport = {
  from_date: string;
  to_date: string;
  items: TopSellingProduct[];
};

export type RefundStatusBreakdown = {
  status: string;
  count: number;
  amount: string;
};

export type RefundReport = {
  from_date: string;
  to_date: string;
  total_refunds: number;
  total_refund_amount: string;
  by_status: RefundStatusBreakdown[];
};

function dateQuery(
  params: Record<string, string | number | undefined>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function getSalesReport(
  params: DateRangeParams = {},
  accessToken?: string | null,
): Promise<SalesReport> {
  return apiFetch<SalesReport>(`/admin/reports/sales${dateQuery(params)}`, {
    accessToken,
  });
}

export function getRevenueReport(
  params: DateRangeParams & { group_by?: "day" | "week" | "month" } = {},
  accessToken?: string | null,
): Promise<RevenueReport> {
  return apiFetch<RevenueReport>(`/admin/reports/revenue${dateQuery(params)}`, {
    accessToken,
  });
}

export function getInventoryReport(
  params: { slow_moving_days?: number } = {},
  accessToken?: string | null,
): Promise<InventoryReport> {
  return apiFetch<InventoryReport>(
    `/admin/reports/inventory${dateQuery(params)}`,
    { accessToken },
  );
}

export function getCustomerReport(
  params: DateRangeParams & { group_by?: "day" | "week" | "month" } = {},
  accessToken?: string | null,
): Promise<CustomerReport> {
  return apiFetch<CustomerReport>(
    `/admin/reports/customers${dateQuery(params)}`,
    { accessToken },
  );
}

export function getTopSellingProducts(
  params: DateRangeParams & { limit?: number } = {},
  accessToken?: string | null,
): Promise<TopSellingProductsReport> {
  return apiFetch<TopSellingProductsReport>(
    `/admin/reports/products/top-selling${dateQuery(params)}`,
    { accessToken },
  );
}

export function getRefundReport(
  params: DateRangeParams = {},
  accessToken?: string | null,
): Promise<RefundReport> {
  return apiFetch<RefundReport>(`/admin/reports/refunds${dateQuery(params)}`, {
    accessToken,
  });
}

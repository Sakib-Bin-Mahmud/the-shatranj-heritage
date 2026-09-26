import { apiFetch } from "@/lib/api-client";
import type { Paginated } from "./types";

export type AddressInput = {
  recipient_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string | null;
  city: string;
  district: string;
  postal_code?: string | null;
  address_type?: "shipping" | "billing" | "both";
};

type AddressChoice =
  | { address_id: string; address?: never }
  | { address_id?: never; address: AddressInput };

export type CheckoutQuoteRequest = AddressChoice & {
  shipping_method: "standard" | "express";
};

export type ShippingOption = {
  method: string;
  label: string;
  rate: string;
  estimated_days: string;
};

export type CheckoutQuote = {
  subtotal: string;
  shipping_amount: string;
  discount_amount: string;
  tax_amount: string;
  total_amount: string;
  shipping_options: ShippingOption[];
};

export type PlaceOrderRequest = AddressChoice & {
  shipping_method: "standard" | "express";
  payment_method: "bkash" | "nagad" | "rocket" | "card" | "cod";
  guest_email?: string;
  guest_phone?: string;
};

export type OrderItem = {
  id: string;
  product_variant_id: string;
  product_name: string;
  sku: string;
  unit_price: string;
  quantity: number;
  line_total: string;
};

export type PaymentSummary = {
  id: string;
  method: string;
  status: string;
  amount: string;
  transaction_id: string | null;
  paid_at: string | null;
};

export type OrderSummary = {
  id: string;
  order_number: string;
  status: string;
  total_amount: string;
  currency: string;
  placed_at: string;
};

export type OrderDetail = {
  id: string;
  order_number: string;
  status: string;
  customer_id: string | null;
  guest_email: string | null;
  guest_phone: string | null;
  subtotal_amount: string;
  discount_amount: string;
  shipping_amount: string;
  tax_amount: string;
  total_amount: string;
  currency: string;
  shipping_address: Record<string, unknown>;
  billing_address: Record<string, unknown> | null;
  placed_at: string;
  items: OrderItem[];
  payments: PaymentSummary[];
};

export type ShipmentInfo = {
  id: string;
  order_id: string;
  courier_name: string | null;
  tracking_number: string | null;
  status: string;
  estimated_delivery_date: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
};

export function getCheckoutQuote(
  input: CheckoutQuoteRequest,
  accessToken?: string | null,
): Promise<CheckoutQuote> {
  return apiFetch<CheckoutQuote>("/checkout/quote", {
    method: "POST",
    body: input,
    accessToken,
  });
}

export type PlaceOrderResult = {
  order: OrderSummary;
  payment: { redirect_url: string } | null;
};

export function placeOrder(
  input: PlaceOrderRequest,
  idempotencyKey: string,
  accessToken?: string | null,
): Promise<PlaceOrderResult> {
  return apiFetch<PlaceOrderResult>("/orders", {
    method: "POST",
    body: input,
    accessToken,
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export function listMyOrders(
  params: { page?: number; limit?: number } = {},
  accessToken?: string | null,
): Promise<Paginated<OrderSummary>> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiFetch<Paginated<OrderSummary>>(
    `/orders${query ? `?${query}` : ""}`,
    {
      accessToken,
    },
  );
}

export function getMyOrder(
  orderNumber: string,
  accessToken?: string | null,
): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/orders/${encodeURIComponent(orderNumber)}`, {
    accessToken,
  });
}

export function cancelMyOrder(
  orderNumber: string,
  accessToken?: string | null,
): Promise<OrderSummary> {
  return apiFetch<OrderSummary>(
    `/orders/${encodeURIComponent(orderNumber)}/cancel`,
    { method: "POST", accessToken },
  );
}

export function getGuestOrder(
  orderNumber: string,
  contact: string,
): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(
    `/orders/guest/${encodeURIComponent(orderNumber)}?contact=${encodeURIComponent(contact)}`,
  );
}

export function getMyOrderShipment(
  orderNumber: string,
  accessToken?: string | null,
): Promise<ShipmentInfo> {
  return apiFetch<ShipmentInfo>(
    `/orders/${encodeURIComponent(orderNumber)}/shipment`,
    { accessToken },
  );
}

// --- Admin -------------------------------------------------------------

export function adminListOrders(
  params: { status?: string; page?: number; limit?: number } = {},
  accessToken?: string | null,
): Promise<Paginated<OrderSummary>> {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.page) search.set("page", String(params.page));
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiFetch<Paginated<OrderSummary>>(
    `/admin/orders${query ? `?${query}` : ""}`,
    { accessToken },
  );
}

export function adminGetOrder(
  orderId: string,
  accessToken?: string | null,
): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/admin/orders/${encodeURIComponent(orderId)}`, {
    accessToken,
  });
}

export function adminUpdateOrderStatus(
  orderId: string,
  status: string,
  accessToken?: string | null,
): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(
    `/admin/orders/${encodeURIComponent(orderId)}/status`,
    { method: "PATCH", body: { status }, accessToken },
  );
}

export type RefundResult = {
  id: string;
  order_id: string;
  payment_id: string;
  amount: string;
  status: string;
  reason: string | null;
};

export function adminCreateRefund(
  orderId: string,
  input: { payment_id: string; amount: string; reason?: string | null },
  accessToken?: string | null,
): Promise<RefundResult> {
  return apiFetch<RefundResult>(
    `/admin/orders/${encodeURIComponent(orderId)}/refund`,
    { method: "POST", body: input, accessToken },
  );
}

export function adminGetShipment(
  orderId: string,
  accessToken?: string | null,
): Promise<ShipmentInfo> {
  return apiFetch<ShipmentInfo>(
    `/admin/orders/${encodeURIComponent(orderId)}/shipment`,
    { accessToken },
  );
}

export function adminAssignShipment(
  orderId: string,
  input: {
    courier_name: string;
    tracking_number?: string | null;
    estimated_delivery_date?: string | null;
  },
  accessToken?: string | null,
): Promise<ShipmentInfo> {
  return apiFetch<ShipmentInfo>(
    `/admin/orders/${encodeURIComponent(orderId)}/shipment`,
    { method: "POST", body: input, accessToken },
  );
}

export function adminUpdateShipmentStatus(
  shipmentId: string,
  status: "dispatched" | "in_transit" | "delivered" | "failed",
  accessToken?: string | null,
): Promise<ShipmentInfo> {
  return apiFetch<ShipmentInfo>(
    `/admin/shipments/${encodeURIComponent(shipmentId)}/status`,
    { method: "PATCH", body: { status }, accessToken },
  );
}

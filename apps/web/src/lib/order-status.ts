import type { BadgeTone } from "@/components/ui";
import type { Dictionary } from "@/i18n/get-dictionary";

const STATUS_TONES: Record<string, BadgeTone> = {
  pending: "neutral",
  awaiting_payment: "warning",
  confirmed: "info",
  packed: "info",
  shipped: "info",
  delivered: "success",
  cancelled: "danger",
  returned: "danger",
  refunded: "neutral",
};

export function orderStatusTone(status: string): BadgeTone {
  return STATUS_TONES[status] ?? "neutral";
}

export function orderStatusLabel(dict: Dictionary, status: string): string {
  const labels = dict.account.orderStatus as Record<string, string>;
  return labels[status] ?? status;
}

// Admin-only: the subset of app/modules/orders/service.py's own
// VALID_TRANSITIONS worth exposing as a direct "change status" action.
// "shipped" and "delivered" are deliberately left out even though the
// backend accepts them here too — each has its own dedicated flow
// (assign a courier; progress the shipment) that keeps the Shipment
// row and notification side effects in sync, which a raw status PATCH
// does not do.
const ADMIN_STATUS_ACTIONS: Record<string, string[]> = {
  pending: ["confirmed", "cancelled"],
  awaiting_payment: ["confirmed", "cancelled"],
  confirmed: ["packed", "cancelled"],
  packed: ["cancelled"],
  shipped: [],
  delivered: [],
  cancelled: [],
  returned: [],
  refunded: [],
};

export function nextAdminOrderStatuses(status: string): string[] {
  return ADMIN_STATUS_ACTIONS[status] ?? [];
}

// Mirrors app/modules/shipping/service.py's SHIPMENT_VALID_TRANSITIONS.
const SHIPMENT_STATUS_ACTIONS: Record<string, string[]> = {
  pending: ["dispatched", "failed"],
  dispatched: ["in_transit", "failed"],
  in_transit: ["delivered", "failed"],
  delivered: [],
  failed: ["dispatched"],
};

export function nextShipmentStatuses(status: string): string[] {
  return SHIPMENT_STATUS_ACTIONS[status] ?? [];
}

const SHIPMENT_STATUS_TONES: Record<string, BadgeTone> = {
  pending: "neutral",
  dispatched: "info",
  in_transit: "info",
  delivered: "success",
  failed: "danger",
};

export function shipmentStatusTone(status: string): BadgeTone {
  return SHIPMENT_STATUS_TONES[status] ?? "neutral";
}

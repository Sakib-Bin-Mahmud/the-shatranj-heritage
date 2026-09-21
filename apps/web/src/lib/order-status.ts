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

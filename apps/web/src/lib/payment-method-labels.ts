import type { Dictionary } from "@/i18n/get-dictionary";

export function paymentMethodLabel(dict: Dictionary, method: string): string {
  const t = dict.checkout.payment;
  const labels: Record<string, string> = {
    bkash: t.optionBkash,
    nagad: t.optionNagad,
    rocket: t.optionRocket,
    card: t.optionCard,
    cod: t.optionCod,
  };
  return labels[method] ?? method;
}

// English-only lookup for the Admin Portal, which is not wired to
// DictionaryProvider (see admin-sidebar-nav.tsx) so it never renders in
// Bangla even if a staff member's browser has a persisted "bn" locale
// from browsing the storefront as a customer.
const PAYMENT_METHOD_LABELS_EN: Record<string, string> = {
  bkash: "bKash",
  nagad: "Nagad",
  rocket: "Rocket",
  card: "Card",
  cod: "Cash on Delivery",
};

export function paymentMethodLabelEn(method: string): string {
  return PAYMENT_METHOD_LABELS_EN[method] ?? method;
}

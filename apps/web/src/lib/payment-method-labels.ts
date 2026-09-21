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

"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { getCheckoutQuote, type CheckoutQuote } from "@/lib/api/orders";
import { Alert, Button, Skeleton } from "@/components/ui";
import type { AddressSelection } from "./address-step";
import { addressChoiceFromSelection } from "./address-choice";
import styles from "./page.module.css";

export function ShippingStep({
  addressSelection,
  accessToken,
  initialMethod,
  onBack,
  onContinue,
}: {
  addressSelection: AddressSelection;
  accessToken: string | null;
  initialMethod: "standard" | "express" | null;
  onBack: () => void;
  onContinue: (method: "standard" | "express", quote: CheckoutQuote) => void;
}) {
  const { dict } = useDictionary();
  const t = dict.checkout.shipping;
  const [method, setMethod] = useState<"standard" | "express">(
    initialMethod ?? "standard",
  );

  const {
    data: quote,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["checkout-quote", addressSelection, method],
    queryFn: () =>
      getCheckoutQuote(
        {
          ...addressChoiceFromSelection(addressSelection),
          shipping_method: method,
        },
        accessToken,
      ),
  });

  return (
    <div className={styles.stepBody}>
      <h2>{t.heading}</h2>

      {isLoading && <Skeleton height="6rem" />}
      {isError && <Alert tone="danger">{t.quoteError}</Alert>}

      {quote &&
        quote.shipping_options.map((option) => (
          <label
            key={option.method}
            className={`${styles.optionCard} ${method === option.method ? styles.optionCardSelected : ""}`}
          >
            <input
              type="radio"
              name="shipping-method"
              checked={method === option.method}
              onChange={() =>
                setMethod(option.method as "standard" | "express")
              }
            />
            <div className={styles.optionCardBody}>
              <span className={styles.optionCardTitle}>
                {option.method === "express" ? t.expressLabel : t.standardLabel}
              </span>
              <span className={styles.optionCardMeta}>
                {t.estimatedDaysLabel}: {option.estimated_days}
              </span>
            </div>
            <span className={styles.optionCardPrice}>৳{option.rate}</span>
          </label>
        ))}

      <div className={styles.actionsRow}>
        <Button variant="ghost" onClick={onBack}>
          {dict.checkout.backButton}
        </Button>
        <Button
          disabled={!quote}
          onClick={() => quote && onContinue(method, quote)}
        >
          {dict.checkout.continueButton}
        </Button>
      </div>
    </div>
  );
}

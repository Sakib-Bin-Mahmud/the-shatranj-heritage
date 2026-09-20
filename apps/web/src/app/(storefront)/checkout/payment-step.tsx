"use client";

import { useState } from "react";
import { useDictionary } from "@/i18n/dictionary-context";
import { Button } from "@/components/ui";
import type { PlaceOrderRequest } from "@/lib/api/orders";
import styles from "./page.module.css";

type PaymentMethod = PlaceOrderRequest["payment_method"];

const METHODS: PaymentMethod[] = ["bkash", "nagad", "rocket", "card", "cod"];

export function PaymentStep({
  initial,
  onBack,
  onContinue,
}: {
  initial: PaymentMethod | null;
  onBack: () => void;
  onContinue: (method: PaymentMethod) => void;
}) {
  const { dict } = useDictionary();
  const t = dict.checkout.payment;
  const [method, setMethod] = useState<PaymentMethod>(initial ?? "cod");

  const labels: Record<PaymentMethod, string> = {
    bkash: t.optionBkash,
    nagad: t.optionNagad,
    rocket: t.optionRocket,
    card: t.optionCard,
    cod: t.optionCod,
  };

  return (
    <div className={styles.stepBody}>
      <h2>{t.heading}</h2>

      {METHODS.map((option) => (
        <label
          key={option}
          className={`${styles.optionCard} ${method === option ? styles.optionCardSelected : ""}`}
        >
          <input
            type="radio"
            name="payment-method"
            checked={method === option}
            onChange={() => setMethod(option)}
          />
          <div className={styles.optionCardBody}>
            <span className={styles.optionCardTitle}>{labels[option]}</span>
          </div>
        </label>
      ))}

      <div className={styles.actionsRow}>
        <Button variant="ghost" onClick={onBack}>
          {dict.checkout.backButton}
        </Button>
        <Button onClick={() => onContinue(method)}>
          {dict.checkout.continueButton}
        </Button>
      </div>
    </div>
  );
}

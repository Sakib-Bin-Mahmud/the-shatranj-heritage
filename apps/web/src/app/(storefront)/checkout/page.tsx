"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import { getCart } from "@/lib/api/cart";
import type { CheckoutQuote, PlaceOrderRequest } from "@/lib/api/orders";
import { Button, EmptyState, Skeleton } from "@/components/ui";
import { AddressStep, type AddressSelection } from "./address-step";
import { ShippingStep } from "./shipping-step";
import { PaymentStep } from "./payment-step";
import { ReviewStep } from "./review-step";
import styles from "./page.module.css";

type Step = "address" | "shipping" | "payment" | "review";
const STEPS: Step[] = ["address", "shipping", "payment", "review"];

export default function CheckoutPage() {
  const { dict } = useDictionary();
  const { status, accessToken } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<Step>("address");
  const [addressSelection, setAddressSelection] =
    useState<AddressSelection | null>(null);
  const [shippingMethod, setShippingMethod] = useState<
    "standard" | "express" | null
  >(null);
  const [quote, setQuote] = useState<CheckoutQuote | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<
    PlaceOrderRequest["payment_method"] | null
  >(null);

  const cartQueryKey = ["cart", accessToken ?? "guest"];
  const { data: cart, isLoading } = useQuery({
    queryKey: cartQueryKey,
    queryFn: () => getCart(accessToken),
    enabled: status !== "loading",
  });

  if (isLoading || status === "loading") {
    return (
      <div className={styles.page}>
        <Skeleton height="20rem" />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className={styles.page}>
        <EmptyState
          title={dict.cart.emptyHeading}
          action={
            <Button onClick={() => router.push("/products")}>
              {dict.cart.emptyAction}
            </Button>
          }
        />
      </div>
    );
  }

  const stepLabels: Record<Step, string> = dict.checkout.steps;
  const currentIndex = STEPS.indexOf(step);

  return (
    <div className={styles.page}>
      <nav className={styles.stepper} aria-label="Checkout steps">
        {STEPS.map((s, index) => (
          <span
            key={s}
            className={`${styles.step} ${
              s === step
                ? styles.stepActive
                : index < currentIndex
                  ? styles.stepDone
                  : ""
            }`}
          >
            <span className={styles.stepIndex}>{index + 1}</span>
            {stepLabels[s]}
          </span>
        ))}
      </nav>

      {step === "address" && (
        <AddressStep
          isAuthenticated={status === "authenticated"}
          accessToken={accessToken}
          initial={addressSelection}
          onContinue={(selection) => {
            setAddressSelection(selection);
            setStep("shipping");
          }}
        />
      )}

      {step === "shipping" && addressSelection && (
        <ShippingStep
          addressSelection={addressSelection}
          accessToken={accessToken}
          initialMethod={shippingMethod}
          onBack={() => setStep("address")}
          onContinue={(method, nextQuote) => {
            setShippingMethod(method);
            setQuote(nextQuote);
            setStep("payment");
          }}
        />
      )}

      {step === "payment" && (
        <PaymentStep
          initial={paymentMethod}
          onBack={() => setStep("shipping")}
          onContinue={(method) => {
            setPaymentMethod(method);
            setStep("review");
          }}
        />
      )}

      {step === "review" &&
        addressSelection &&
        shippingMethod &&
        quote &&
        paymentMethod && (
          <ReviewStep
            cart={cart}
            addressSelection={addressSelection}
            shippingMethod={shippingMethod}
            quote={quote}
            paymentMethod={paymentMethod}
            accessToken={accessToken}
            onBack={() => setStep("payment")}
            onPlaced={({ orderNumber, redirectUrl }) => {
              if (redirectUrl) {
                window.location.href = redirectUrl;
              } else {
                router.push(
                  `/checkout/confirmation?order=${orderNumber}&status=cod`,
                );
              }
            }}
          />
        )}
    </div>
  );
}

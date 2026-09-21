"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { listMyAddresses } from "@/lib/api/customers";
import {
  placeOrder,
  type CheckoutQuote,
  type PlaceOrderRequest,
} from "@/lib/api/orders";
import { ApiClientError } from "@/lib/api-client";
import {
  getOrCreateIdempotencyKey,
  resetIdempotencyKey,
} from "@/lib/idempotency";
import { setGuestOrderContact } from "@/lib/guest-order-contact";
import { paymentMethodLabel } from "@/lib/payment-method-labels";
import { Alert, Button } from "@/components/ui";
import type { Cart } from "@/lib/api/cart";
import type { AddressSelection } from "./address-step";
import { addressChoiceFromSelection } from "./address-choice";
import styles from "./page.module.css";

export function ReviewStep({
  cart,
  addressSelection,
  shippingMethod,
  quote,
  paymentMethod,
  accessToken,
  onBack,
  onPlaced,
}: {
  cart: Cart;
  addressSelection: AddressSelection;
  shippingMethod: "standard" | "express";
  quote: CheckoutQuote;
  paymentMethod: PlaceOrderRequest["payment_method"];
  accessToken: string | null;
  onBack: () => void;
  onPlaced: (result: {
    orderNumber: string;
    redirectUrl: string | null;
  }) => void;
}) {
  const { dict } = useDictionary();
  const t = dict.checkout.review;
  const queryClient = useQueryClient();

  const { data: addresses } = useQuery({
    queryKey: ["my-addresses"],
    queryFn: () => listMyAddresses(accessToken),
    enabled: addressSelection.kind === "saved",
  });

  const savedAddress =
    addressSelection.kind === "saved"
      ? addresses?.find((a) => a.id === addressSelection.addressId)
      : null;

  const placeOrderMutation = useMutation({
    mutationFn: () => {
      const contact =
        addressSelection.kind === "inline"
          ? (addressSelection.guestEmail ?? addressSelection.guestPhone)
          : undefined;
      if (contact) setGuestOrderContact(contact);

      const request: PlaceOrderRequest = {
        ...addressChoiceFromSelection(addressSelection),
        shipping_method: shippingMethod,
        payment_method: paymentMethod,
        guest_email:
          addressSelection.kind === "inline"
            ? addressSelection.guestEmail
            : undefined,
        guest_phone:
          addressSelection.kind === "inline"
            ? addressSelection.guestPhone
            : undefined,
      };
      return placeOrder(request, getOrCreateIdempotencyKey(), accessToken);
    },
    onSuccess: (result) => {
      resetIdempotencyKey();
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      onPlaced({
        orderNumber: result.order.order_number,
        redirectUrl: result.payment?.redirect_url ?? null,
      });
    },
  });

  return (
    <div className={styles.stepBody}>
      <h2>{t.heading}</h2>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.addressHeading}</span>
        {addressSelection.kind === "saved" && savedAddress ? (
          <span>
            {savedAddress.recipient_name} — {savedAddress.address_line1},{" "}
            {savedAddress.city}, {savedAddress.district}
          </span>
        ) : addressSelection.kind === "inline" ? (
          <span>
            {addressSelection.address.recipient_name} —{" "}
            {addressSelection.address.address_line1},{" "}
            {addressSelection.address.city}, {addressSelection.address.district}
          </span>
        ) : null}
      </div>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.shippingHeading}</span>
        <span>
          {shippingMethod === "express"
            ? dict.checkout.shipping.expressLabel
            : dict.checkout.shipping.standardLabel}{" "}
          — ৳{quote.shipping_amount}
        </span>
      </div>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.paymentHeading}</span>
        <span>{paymentMethodLabel(dict, paymentMethod)}</span>
      </div>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.itemsHeading}</span>
        {cart.items.map((item) => (
          <div key={item.id} className={styles.reviewItemRow}>
            <span>
              {item.product_name} × {item.quantity}
            </span>
            <span>৳{item.line_total}</span>
          </div>
        ))}
      </div>

      <div className={styles.summary}>
        <div className={styles.summaryRow}>
          <span>{dict.cart.subtotalLabel}</span>
          <span>৳{quote.subtotal}</span>
        </div>
        <div className={styles.summaryRow}>
          <span>{dict.cart.shippingLabel}</span>
          <span>৳{quote.shipping_amount}</span>
        </div>
        <div className={styles.summaryRow}>
          <span>{dict.cart.taxLabel}</span>
          <span>৳{quote.tax_amount}</span>
        </div>
        {Number(quote.discount_amount) > 0 && (
          <div className={styles.summaryRow}>
            <span>{dict.cart.discountLabel}</span>
            <span>-৳{quote.discount_amount}</span>
          </div>
        )}
        <div className={styles.summaryTotal}>
          <span>{dict.cart.totalLabel}</span>
          <span>৳{quote.total_amount}</span>
        </div>
      </div>

      {placeOrderMutation.isError && (
        <Alert tone="danger">
          {placeOrderMutation.error instanceof ApiClientError
            ? placeOrderMutation.error.message
            : t.orderError}
        </Alert>
      )}

      <div className={styles.actionsRow}>
        <Button
          variant="ghost"
          onClick={onBack}
          disabled={placeOrderMutation.isPending}
        >
          {dict.checkout.backButton}
        </Button>
        <Button
          disabled={placeOrderMutation.isPending}
          onClick={() => placeOrderMutation.mutate()}
        >
          {placeOrderMutation.isPending ? t.placingOrder : t.placeOrderButton}
        </Button>
      </div>
    </div>
  );
}

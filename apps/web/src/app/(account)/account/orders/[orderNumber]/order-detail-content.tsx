"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import {
  cancelMyOrder,
  getMyOrder,
  getMyOrderShipment,
} from "@/lib/api/orders";
import { initiatePayment } from "@/lib/api/payments";
import { ApiClientError } from "@/lib/api-client";
import { orderStatusLabel, orderStatusTone } from "@/lib/order-status";
import { paymentMethodLabel } from "@/lib/payment-method-labels";
import { Alert, Badge, Button, Modal, Skeleton } from "@/components/ui";
import styles from "./page.module.css";

const CANCELLABLE_STATUSES = new Set([
  "pending",
  "awaiting_payment",
  "confirmed",
  "packed",
]);

const RETRY_METHODS = ["bkash", "nagad", "rocket", "card"] as const;
type RetryMethod = (typeof RETRY_METHODS)[number];

function addressLine(address: Record<string, unknown>): string {
  const get = (key: string) =>
    typeof address[key] === "string" ? (address[key] as string) : "";
  return [
    get("address_line1"),
    get("address_line2"),
    get("city"),
    get("district"),
  ]
    .filter(Boolean)
    .join(", ");
}

export function OrderDetailContent() {
  const params = useParams<{ orderNumber: string }>();
  const orderNumber = params.orderNumber;
  const { status: authStatus, accessToken } = useAuth();
  const router = useRouter();
  const { dict } = useDictionary();
  const t = dict.account.orderDetail;
  const queryClient = useQueryClient();

  useEffect(() => {
    if (authStatus === "unauthenticated") router.push("/login");
  }, [authStatus, router]);

  const {
    data: order,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["order-detail", orderNumber, accessToken],
    queryFn: () => getMyOrder(orderNumber, accessToken),
    enabled: authStatus === "authenticated" && Boolean(orderNumber),
  });

  const { data: shipment } = useQuery({
    queryKey: ["order-shipment", orderNumber, accessToken],
    queryFn: () => getMyOrderShipment(orderNumber, accessToken),
    enabled: authStatus === "authenticated" && Boolean(order),
    retry: false,
  });

  const [cancelOpen, setCancelOpen] = useState(false);
  const cancelMutation = useMutation({
    mutationFn: () => cancelMyOrder(orderNumber, accessToken),
    onSuccess: () => {
      setCancelOpen(false);
      queryClient.invalidateQueries({
        queryKey: ["order-detail", orderNumber],
      });
      queryClient.invalidateQueries({ queryKey: ["my-orders"] });
    },
  });

  const [retryMethod, setRetryMethod] = useState<RetryMethod>("bkash");
  const retryMutation = useMutation({
    mutationFn: () => {
      if (!order) throw new Error("Order not loaded");
      return initiatePayment(
        { order_id: order.id, method: retryMethod },
        accessToken,
      );
    },
    onSuccess: (result) => {
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
      }
    },
  });

  if (authStatus === "loading" || isLoading) {
    return (
      <div className={styles.page}>
        <Skeleton height="20rem" />
      </div>
    );
  }

  if (isError || !order) {
    return (
      <div className={styles.page}>
        <h1>{t.notFound}</h1>
        <Link href="/account?tab=orders">{t.backButton}</Link>
      </div>
    );
  }

  const isCancellable = CANCELLABLE_STATUSES.has(order.status);
  const hasSuccessfulPayment = order.payments.some(
    (p) => p.status === "successful",
  );
  const latestPayment = order.payments[order.payments.length - 1];
  const canRetryPayment =
    order.status === "awaiting_payment" &&
    !hasSuccessfulPayment &&
    Boolean(latestPayment) &&
    latestPayment.method !== "cod";

  return (
    <div className={styles.page}>
      <Link href="/account?tab=orders" className={styles.backLink}>
        {t.backButton}
      </Link>

      <div className={styles.headingRow}>
        <h1>
          {t.heading} {order.order_number}
        </h1>
        <Badge tone={orderStatusTone(order.status)}>
          {orderStatusLabel(dict, order.status)}
        </Badge>
      </div>
      <p className={styles.placedOn}>
        {t.placedOnLabel}: {new Date(order.placed_at).toLocaleString()}
      </p>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.itemsHeading}</span>
        {order.items.map((item) => (
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
          <span>৳{order.subtotal_amount}</span>
        </div>
        <div className={styles.summaryRow}>
          <span>{dict.cart.shippingLabel}</span>
          <span>৳{order.shipping_amount}</span>
        </div>
        <div className={styles.summaryRow}>
          <span>{dict.cart.taxLabel}</span>
          <span>৳{order.tax_amount}</span>
        </div>
        {Number(order.discount_amount) > 0 && (
          <div className={styles.summaryRow}>
            <span>{dict.cart.discountLabel}</span>
            <span>-৳{order.discount_amount}</span>
          </div>
        )}
        <div className={styles.summaryTotal}>
          <span>{dict.cart.totalLabel}</span>
          <span>৳{order.total_amount}</span>
        </div>
      </div>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>
          {t.shippingAddressHeading}
        </span>
        <span>{addressLine(order.shipping_address)}</span>
      </div>

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.paymentHeading}</span>
        {order.payments.map((payment) => (
          <div key={payment.id} className={styles.reviewItemRow}>
            <span>{paymentMethodLabel(dict, payment.method)}</span>
            <span>
              {t.paymentStatusLabel}: {payment.status}
            </span>
          </div>
        ))}
      </div>

      {shipment && (
        <div className={styles.reviewSection}>
          <span className={styles.reviewSectionHeading}>
            {t.trackingHeading}
          </span>
          <span>
            {t.trackingCourierLabel}: {shipment.courier_name}
          </span>
          <span>
            {t.trackingNumberLabel}: {shipment.tracking_number}
          </span>
          <span>
            {t.trackingStatusLabel}: {shipment.status}
          </span>
          {shipment.estimated_delivery_date && (
            <span>
              {t.trackingEtaLabel}:{" "}
              {new Date(shipment.estimated_delivery_date).toLocaleDateString()}
            </span>
          )}
        </div>
      )}

      {canRetryPayment && (
        <div className={styles.reviewSection}>
          <span className={styles.reviewSectionHeading}>{t.retryHeading}</span>
          <p>{t.retryBody}</p>
          <div className={styles.retryOptions}>
            {RETRY_METHODS.map((method) => (
              <label
                key={method}
                className={`${styles.optionCard} ${
                  retryMethod === method ? styles.optionCardSelected : ""
                }`}
              >
                <input
                  type="radio"
                  name="retry-method"
                  checked={retryMethod === method}
                  onChange={() => setRetryMethod(method)}
                />
                <span>{paymentMethodLabel(dict, method)}</span>
              </label>
            ))}
          </div>
          {retryMutation.isError && (
            <Alert tone="danger">
              {retryMutation.error instanceof ApiClientError
                ? retryMutation.error.message
                : t.retryError}
            </Alert>
          )}
          <Button
            onClick={() => retryMutation.mutate()}
            disabled={retryMutation.isPending}
          >
            {t.retryButton}
          </Button>
        </div>
      )}

      <div className={styles.reviewSection}>
        <span className={styles.reviewSectionHeading}>{t.cancelHeading}</span>
        {isCancellable ? (
          <>
            <p>{t.cancelBody}</p>
            <Button variant="danger" onClick={() => setCancelOpen(true)}>
              {t.cancelButton}
            </Button>
          </>
        ) : (
          <p>{t.notCancellableExplanation}</p>
        )}
        {cancelMutation.isError && (
          <Alert tone="danger">
            {cancelMutation.error instanceof ApiClientError
              ? cancelMutation.error.message
              : t.cancelError}
          </Alert>
        )}
      </div>

      <Modal
        open={cancelOpen}
        onClose={() => setCancelOpen(false)}
        title={t.cancelConfirmTitle}
      >
        <p>{t.cancelConfirmBody}</p>
        <div className={styles.actionsRow}>
          <Button variant="ghost" onClick={() => setCancelOpen(false)}>
            {t.cancelDismissButton}
          </Button>
          <Button
            variant="danger"
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
          >
            {t.cancelConfirmButton}
          </Button>
        </div>
      </Modal>
    </div>
  );
}

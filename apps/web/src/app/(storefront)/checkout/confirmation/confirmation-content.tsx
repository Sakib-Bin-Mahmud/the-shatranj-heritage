"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import { getGuestOrder, getMyOrder } from "@/lib/api/orders";
import { getGuestOrderContact } from "@/lib/guest-order-contact";
import { Button, Skeleton } from "@/components/ui";
import styles from "./page.module.css";

const MAX_POLL_ATTEMPTS = 20;
const POLL_INTERVAL_MS = 3000;

export function ConfirmationContent() {
  const { dict } = useDictionary();
  const t = dict.orderConfirmation;
  const { status: authStatus, accessToken } = useAuth();
  const searchParams = useSearchParams();
  const orderNumber = searchParams.get("order");
  const redirectStatus = searchParams.get("status");

  const [contact] = useState(() => getGuestOrderContact());
  const attemptsRef = useRef(0);

  const isAuthenticated = authStatus === "authenticated";
  const canLookUp =
    Boolean(orderNumber) && (isAuthenticated || Boolean(contact));

  const { data: order, isLoading } = useQuery({
    queryKey: ["order-confirmation", orderNumber, accessToken ?? contact],
    queryFn: () =>
      isAuthenticated
        ? getMyOrder(orderNumber!, accessToken)
        : getGuestOrder(orderNumber!, contact!),
    enabled: canLookUp && authStatus !== "loading",
    refetchInterval: (query) => {
      if (redirectStatus !== "success") return false;
      if (attemptsRef.current >= MAX_POLL_ATTEMPTS) return false;
      const data = query.state.data;
      if (data && data.status !== "awaiting_payment") return false;
      attemptsRef.current += 1;
      return POLL_INTERVAL_MS;
    },
  });

  const [pollTimedOut, setPollTimedOut] = useState(false);
  useEffect(() => {
    if (
      redirectStatus === "success" &&
      order?.status === "awaiting_payment" &&
      attemptsRef.current >= MAX_POLL_ATTEMPTS
    ) {
      setPollTimedOut(true);
    }
  }, [order?.status, redirectStatus]);

  if (!orderNumber) {
    return (
      <div className={styles.page}>
        <h1>{t.notFoundHeading}</h1>
        <Link href="/products">{t.continueShoppingButton}</Link>
      </div>
    );
  }

  const stillConfirming =
    redirectStatus === "success" &&
    (!order || order.status === "awaiting_payment") &&
    !pollTimedOut;

  if (canLookUp && (isLoading || stillConfirming)) {
    return (
      <div className={styles.page}>
        <h1>{t.confirmingHeading}</h1>
        <p>{t.confirmingBody}</p>
        <Skeleton height="8rem" />
      </div>
    );
  }

  const { heading, body } = resolveOutcome(redirectStatus, t);

  return (
    <div className={styles.page}>
      <h1>{heading}</h1>
      <p>{body}</p>

      <div className={styles.summary}>
        <div className={styles.summaryRow}>
          <span>{t.orderNumberLabel}</span>
          <span className={styles.orderNumber}>{orderNumber}</span>
        </div>
        {order && (
          <div className={styles.summaryRow}>
            <span>{t.totalLabel}</span>
            <span>৳{order.total_amount}</span>
          </div>
        )}
      </div>

      <div className={styles.actions}>
        {isAuthenticated && order && (
          <Link href={`/account/orders/${order.order_number}`}>
            <Button>{t.viewOrdersButton}</Button>
          </Link>
        )}
        <Link href="/products">
          <Button variant="secondary">{t.continueShoppingButton}</Button>
        </Link>
      </div>
    </div>
  );
}

function resolveOutcome(
  redirectStatus: string | null,
  t: ReturnType<typeof useDictionary>["dict"]["orderConfirmation"],
): { heading: string; body: string } {
  if (redirectStatus === "cod") {
    return { heading: t.codHeading, body: t.codBody };
  }
  if (redirectStatus === "failed") {
    return { heading: t.failedHeading, body: t.failedBody };
  }
  if (redirectStatus === "cancelled") {
    return { heading: t.cancelledHeading, body: t.cancelledBody };
  }
  // redirectStatus === "success", and no longer "still confirming" (the
  // gate above only lets this branch render once the order has left
  // awaiting_payment, or polling timed out) — either way there's
  // nothing more specific than "confirmed" left to say here.
  return { heading: t.successHeading, body: t.successBody };
}

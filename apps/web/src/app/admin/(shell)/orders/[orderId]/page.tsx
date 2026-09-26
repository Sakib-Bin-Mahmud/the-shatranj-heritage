"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminGetOrder } from "@/lib/api/orders";
import { orderStatusTone } from "@/lib/order-status";
import { titleCase } from "@/lib/text-format";
import { paymentMethodLabelEn } from "@/lib/payment-method-labels";
import { addressLine } from "@/lib/format-address";
import { Badge, Skeleton } from "@/components/ui";
import { StatusSection } from "./status-section";
import { ShipmentSection } from "./shipment-section";
import { RefundSection } from "./refund-section";
import styles from "../page.module.css";

export default function AdminOrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const { accessToken } = useAdminAuth();

  const {
    data: order,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["admin-order", orderId],
    queryFn: () => adminGetOrder(orderId, accessToken),
  });

  if (isLoading) {
    return (
      <div className={styles.page}>
        <Skeleton height="20rem" />
      </div>
    );
  }

  if (isError || !order) {
    return (
      <div className={styles.page}>
        <h1>Order not found</h1>
        <Link href="/admin/orders">Back to orders</Link>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link href="/admin/orders" className={styles.backLink}>
        Back to orders
      </Link>

      <div className={styles.headingRow}>
        <h1>Order {order.order_number}</h1>
        <Badge tone={orderStatusTone(order.status)}>
          {titleCase(order.status)}
        </Badge>
      </div>
      <p className={styles.placedOn}>
        Placed: {new Date(order.placed_at).toLocaleString()}
      </p>

      <div className={styles.section}>
        <span className={styles.sectionHeading}>Items</span>
        {order.items.map((item) => (
          <div key={item.id} className={styles.itemRow}>
            <span>
              {item.product_name} × {item.quantity}
            </span>
            <span>৳{item.line_total}</span>
          </div>
        ))}
      </div>

      <div className={styles.section}>
        <span className={styles.sectionHeading}>Summary</span>
        <div className={styles.itemRow}>
          <span>Subtotal</span>
          <span>৳{order.subtotal_amount}</span>
        </div>
        <div className={styles.itemRow}>
          <span>Shipping</span>
          <span>৳{order.shipping_amount}</span>
        </div>
        <div className={styles.itemRow}>
          <span>Tax</span>
          <span>৳{order.tax_amount}</span>
        </div>
        {Number(order.discount_amount) > 0 && (
          <div className={styles.itemRow}>
            <span>Discount</span>
            <span>-৳{order.discount_amount}</span>
          </div>
        )}
        <div className={styles.itemRow}>
          <strong>Total</strong>
          <strong>৳{order.total_amount}</strong>
        </div>
      </div>

      <div className={styles.section}>
        <span className={styles.sectionHeading}>Customer</span>
        <span>
          {order.guest_email ?? order.guest_phone ?? "Registered customer"}
        </span>
        <span>{addressLine(order.shipping_address)}</span>
      </div>

      <div className={styles.section}>
        <span className={styles.sectionHeading}>Payments</span>
        {order.payments.map((payment) => (
          <div key={payment.id} className={styles.itemRow}>
            <span>{paymentMethodLabelEn(payment.method)}</span>
            <span>{titleCase(payment.status)}</span>
          </div>
        ))}
      </div>

      <StatusSection order={order} />
      <ShipmentSection order={order} />
      <RefundSection order={order} />
    </div>
  );
}

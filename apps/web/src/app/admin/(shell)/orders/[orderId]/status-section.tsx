"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminUpdateOrderStatus, type OrderDetail } from "@/lib/api/orders";
import { nextAdminOrderStatuses } from "@/lib/order-status";
import { titleCase } from "@/lib/text-format";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Button, Modal } from "@/components/ui";
import styles from "../page.module.css";

export function StatusSection({ order }: { order: OrderDetail }) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (status: string) =>
      adminUpdateOrderStatus(order.id, status, accessToken),
    onSuccess: () => {
      setConfirming(null);
      queryClient.invalidateQueries({ queryKey: ["admin-order", order.id] });
      queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    },
  });

  const nextStatuses = nextAdminOrderStatuses(order.status);
  if (nextStatuses.length === 0) return null;

  return (
    <div className={styles.section}>
      <span className={styles.sectionHeading}>Change status</span>
      <div className={styles.actionsRow}>
        {nextStatuses.map((status) => (
          <Button
            key={status}
            variant={status === "cancelled" ? "danger" : "secondary"}
            onClick={() => setConfirming(status)}
          >
            Mark as {titleCase(status)}
          </Button>
        ))}
      </div>

      <Modal
        open={Boolean(confirming)}
        onClose={() => setConfirming(null)}
        title={`Mark order as ${confirming ? titleCase(confirming) : ""}?`}
      >
        <p>
          {confirming === "cancelled"
            ? "This releases reserved stock and requests a refund automatically if the order was already paid."
            : "This updates the order's status."}
        </p>
        {mutation.isError && (
          <Alert tone="danger">
            {mutation.error instanceof ApiClientError
              ? mutation.error.message
              : "Could not update this order's status."}
          </Alert>
        )}
        <div className={styles.modalActions}>
          <Button variant="ghost" onClick={() => setConfirming(null)}>
            Cancel
          </Button>
          <Button
            variant={confirming === "cancelled" ? "danger" : "primary"}
            disabled={mutation.isPending}
            onClick={() => confirming && mutation.mutate(confirming)}
          >
            Confirm
          </Button>
        </div>
      </Modal>
    </div>
  );
}

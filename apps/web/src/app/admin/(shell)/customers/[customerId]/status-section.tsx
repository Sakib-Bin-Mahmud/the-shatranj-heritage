"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminUpdateCustomerStatus,
  type CustomerProfile,
} from "@/lib/api/customers";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Button, Modal } from "@/components/ui";
import styles from "../page.module.css";

export function CustomerStatusSection({
  customer,
}: {
  customer: CustomerProfile;
}) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState<"active" | "suspended" | null>(
    null,
  );

  const mutation = useMutation({
    mutationFn: (status: "active" | "suspended") =>
      adminUpdateCustomerStatus(customer.id, status, accessToken),
    onSuccess: () => {
      setConfirming(null);
      queryClient.invalidateQueries({
        queryKey: ["admin-customer", customer.id],
      });
      queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
    },
  });

  return (
    <div className={styles.section}>
      <span className={styles.sectionHeading}>Account status</span>
      <div className={styles.actionsRow}>
        {customer.status === "active" ? (
          <Button variant="danger" onClick={() => setConfirming("suspended")}>
            Suspend account
          </Button>
        ) : (
          <Button variant="secondary" onClick={() => setConfirming("active")}>
            Reactivate account
          </Button>
        )}
      </div>

      <Modal
        open={Boolean(confirming)}
        onClose={() => setConfirming(null)}
        title={
          confirming === "suspended"
            ? "Suspend this customer's account?"
            : "Reactivate this customer's account?"
        }
      >
        <p>
          {confirming === "suspended"
            ? "The customer will be signed out and unable to log in until reactivated."
            : "The customer will be able to log in again."}
        </p>
        {mutation.isError && (
          <Alert tone="danger">
            {mutation.error instanceof ApiClientError
              ? mutation.error.message
              : "Could not update this customer's status."}
          </Alert>
        )}
        <div className={styles.modalActions}>
          <Button variant="ghost" onClick={() => setConfirming(null)}>
            Cancel
          </Button>
          <Button
            variant={confirming === "suspended" ? "danger" : "primary"}
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

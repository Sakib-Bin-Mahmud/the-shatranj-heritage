"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import {
  adminCreateRefund,
  type OrderDetail,
  type RefundResult,
} from "@/lib/api/orders";
import { titleCase } from "@/lib/text-format";
import { ApiClientError } from "@/lib/api-client";
import { Alert, Button, Modal, SelectField, TextField } from "@/components/ui";
import styles from "../page.module.css";

export function RefundSection({ order }: { order: OrderDetail }) {
  const { accessToken } = useAdminAuth();
  const successfulPayments = order.payments.filter(
    (p) => p.status === "successful",
  );

  const [open, setOpen] = useState(false);
  const [paymentId, setPaymentId] = useState("");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [result, setResult] = useState<RefundResult | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      adminCreateRefund(
        order.id,
        { payment_id: paymentId, amount, reason: reason || undefined },
        accessToken,
      ),
    onSuccess: (r) => setResult(r),
  });

  if (successfulPayments.length === 0) return null;

  function openModal() {
    setResult(null);
    setPaymentId(successfulPayments[0].id);
    setAmount(successfulPayments[0].amount);
    setReason("");
    setOpen(true);
  }

  return (
    <div className={styles.section}>
      <span className={styles.sectionHeading}>Refunds</span>
      <p>
        Issue a refund request against a successful payment. Approval and money
        movement happen outside this system.
      </p>
      <Button variant="danger" onClick={openModal}>
        Request refund
      </Button>

      <Modal open={open} onClose={() => setOpen(false)} title="Request refund">
        {result ? (
          <div className={styles.modalForm}>
            <Alert tone="success">
              Refund requested — status: {titleCase(result.status)}.
            </Alert>
            <div className={styles.modalActions}>
              <Button onClick={() => setOpen(false)}>Done</Button>
            </div>
          </div>
        ) : (
          <form
            className={styles.modalForm}
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <SelectField
              label="Payment"
              value={paymentId}
              onChange={(e) => setPaymentId(e.target.value)}
            >
              {successfulPayments.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.method} — ৳{p.amount}
                </option>
              ))}
            </SelectField>
            <TextField
              label="Amount (৳)"
              required
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <TextField
              label="Reason (optional)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            {mutation.isError && (
              <Alert tone="danger">
                {mutation.error instanceof ApiClientError
                  ? mutation.error.message
                  : "Could not request this refund."}
              </Alert>
            )}
            <div className={styles.modalActions}>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                Request refund
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}

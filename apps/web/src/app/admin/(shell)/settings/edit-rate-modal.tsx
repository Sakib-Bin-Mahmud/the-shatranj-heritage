"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { adminUpdateShippingRate, type ShippingRate } from "@/lib/api/settings";
import { ApiClientError } from "@/lib/api-client";
import {
  Alert,
  Button,
  CheckboxField,
  Modal,
  TextField,
} from "@/components/ui";
import styles from "./page.module.css";

function EditRateForm({
  rate,
  onClose,
}: {
  rate: ShippingRate;
  onClose: () => void;
}) {
  const { accessToken } = useAdminAuth();
  const queryClient = useQueryClient();
  const [baseRate, setBaseRate] = useState(rate.base_rate);
  const [baseWeight, setBaseWeight] = useState(String(rate.base_weight_grams));
  const [perKgRate, setPerKgRate] = useState(rate.per_kg_rate);
  const [isActive, setIsActive] = useState(rate.is_active);

  const mutation = useMutation({
    mutationFn: () =>
      adminUpdateShippingRate(
        rate.id,
        {
          base_rate: baseRate,
          base_weight_grams: Number(baseWeight),
          per_kg_rate: perKgRate,
          is_active: isActive,
        },
        accessToken,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-shipping-rates"] });
      onClose();
    },
  });

  return (
    <form
      className={styles.modalForm}
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
    >
      <TextField
        label="Base rate (৳)"
        required
        inputMode="decimal"
        value={baseRate}
        onChange={(e) => setBaseRate(e.target.value)}
      />
      <TextField
        label="Base weight (grams)"
        required
        inputMode="numeric"
        value={baseWeight}
        onChange={(e) => setBaseWeight(e.target.value)}
        hint="Weight included in the base rate before per-kg pricing applies."
      />
      <TextField
        label="Per-kg rate (৳)"
        required
        inputMode="decimal"
        value={perKgRate}
        onChange={(e) => setPerKgRate(e.target.value)}
      />
      <CheckboxField
        label="Active"
        checked={isActive}
        onChange={(e) => setIsActive(e.target.checked)}
      />
      {mutation.isError && (
        <Alert tone="danger">
          {mutation.error instanceof ApiClientError
            ? mutation.error.message
            : "Could not update this shipping rate."}
        </Alert>
      )}
      <div className={styles.modalActions}>
        <Button type="button" variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={mutation.isPending}>
          Save changes
        </Button>
      </div>
    </form>
  );
}

export function EditRateModal({
  rate,
  onClose,
}: {
  rate: ShippingRate | null;
  onClose: () => void;
}) {
  return (
    <Modal
      open={Boolean(rate)}
      onClose={onClose}
      title={rate ? `Edit ${rate.zone} — ${rate.method}` : "Edit shipping rate"}
    >
      {rate && <EditRateForm key={rate.id} rate={rate} onClose={onClose} />}
    </Modal>
  );
}

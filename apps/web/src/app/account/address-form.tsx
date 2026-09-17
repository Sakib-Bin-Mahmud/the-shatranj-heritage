"use client";

import { useState, type FormEvent } from "react";
import formStyles from "@/components/form.module.css";

export type AddressInput = {
  label: string;
  recipient_name: string;
  phone: string;
  address_line1: string;
  address_line2: string;
  city: string;
  district: string;
  postal_code: string;
  country: string;
  address_type: "shipping" | "billing" | "both";
  is_default: boolean;
};

const emptyAddress: AddressInput = {
  label: "",
  recipient_name: "",
  phone: "",
  address_line1: "",
  address_line2: "",
  city: "",
  district: "",
  postal_code: "",
  country: "BD",
  address_type: "shipping",
  is_default: false,
};

export function AddressForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<AddressInput>;
  submitLabel: string;
  onSubmit: (input: AddressInput) => Promise<void>;
  onCancel?: () => void;
}) {
  const [values, setValues] = useState<AddressInput>({
    ...emptyAddress,
    ...initial,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof AddressInput>(
    key: K,
    value: AddressInput[K],
  ) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(values);
    } catch {
      setError("Could not save this address.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className={formStyles.form} onSubmit={handleSubmit}>
      <label>
        Label (optional)
        <input
          value={values.label}
          onChange={(e) => update("label", e.target.value)}
          placeholder="Home, Office…"
        />
      </label>
      <label>
        Recipient name
        <input
          required
          value={values.recipient_name}
          onChange={(e) => update("recipient_name", e.target.value)}
        />
      </label>
      <label>
        Phone
        <input
          required
          value={values.phone}
          onChange={(e) => update("phone", e.target.value)}
        />
      </label>
      <label>
        Address line 1
        <input
          required
          value={values.address_line1}
          onChange={(e) => update("address_line1", e.target.value)}
        />
      </label>
      <label>
        Address line 2 (optional)
        <input
          value={values.address_line2}
          onChange={(e) => update("address_line2", e.target.value)}
        />
      </label>
      <label>
        City
        <input
          required
          value={values.city}
          onChange={(e) => update("city", e.target.value)}
        />
      </label>
      <label>
        District
        <input
          required
          value={values.district}
          onChange={(e) => update("district", e.target.value)}
        />
      </label>
      <label>
        Postal code (optional)
        <input
          value={values.postal_code}
          onChange={(e) => update("postal_code", e.target.value)}
        />
      </label>
      <label>
        Address type
        <select
          value={values.address_type}
          onChange={(e) =>
            update(
              "address_type",
              e.target.value as AddressInput["address_type"],
            )
          }
        >
          <option value="shipping">Shipping</option>
          <option value="billing">Billing</option>
          <option value="both">Both</option>
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={values.is_default}
          onChange={(e) => update("is_default", e.target.checked)}
        />{" "}
        Set as default address
      </label>

      {error && <p className={formStyles.error}>{error}</p>}

      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

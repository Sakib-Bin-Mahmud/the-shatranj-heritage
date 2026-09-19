"use client";

import { useState, type FormEvent } from "react";
import { useDictionary } from "@/i18n/dictionary-context";
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
  const { dict } = useDictionary();
  const t = dict.account.addresses.form;
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
      setError(t.genericError);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className={formStyles.form} onSubmit={handleSubmit}>
      <label>
        {t.labelOptional}
        <input
          value={values.label}
          onChange={(e) => update("label", e.target.value)}
          placeholder={t.labelPlaceholder}
        />
      </label>
      <label>
        {t.recipientNameLabel}
        <input
          required
          autoComplete="name"
          value={values.recipient_name}
          onChange={(e) => update("recipient_name", e.target.value)}
        />
      </label>
      <label>
        {t.phoneLabel}
        <input
          required
          autoComplete="tel"
          value={values.phone}
          onChange={(e) => update("phone", e.target.value)}
        />
      </label>
      <label>
        {t.addressLine1Label}
        <input
          required
          autoComplete="address-line1"
          value={values.address_line1}
          onChange={(e) => update("address_line1", e.target.value)}
        />
      </label>
      <label>
        {t.addressLine2Label}
        <input
          autoComplete="address-line2"
          value={values.address_line2}
          onChange={(e) => update("address_line2", e.target.value)}
        />
      </label>
      <label>
        {t.cityLabel}
        <input
          required
          autoComplete="address-level2"
          value={values.city}
          onChange={(e) => update("city", e.target.value)}
        />
      </label>
      <label>
        {t.districtLabel}
        <input
          required
          autoComplete="address-level1"
          value={values.district}
          onChange={(e) => update("district", e.target.value)}
        />
      </label>
      <label>
        {t.postalCodeLabel}
        <input
          autoComplete="postal-code"
          value={values.postal_code}
          onChange={(e) => update("postal_code", e.target.value)}
        />
      </label>
      <label>
        {t.addressTypeLabel}
        <select
          value={values.address_type}
          onChange={(e) =>
            update(
              "address_type",
              e.target.value as AddressInput["address_type"],
            )
          }
        >
          <option value="shipping">{t.optionShipping}</option>
          <option value="billing">{t.optionBilling}</option>
          <option value="both">{t.optionBoth}</option>
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={values.is_default}
          onChange={(e) => update("is_default", e.target.checked)}
        />{" "}
        {t.setDefaultLabel}
      </label>

      {error && (
        <p className={formStyles.error} role="alert">
          {error}
        </p>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" disabled={submitting}>
          {submitting ? dict.common.saving : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} disabled={submitting}>
            {dict.common.cancel}
          </button>
        )}
      </div>
    </form>
  );
}

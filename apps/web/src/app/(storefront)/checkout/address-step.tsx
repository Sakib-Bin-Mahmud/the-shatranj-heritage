"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { listMyAddresses, type Address } from "@/lib/api/customers";
import {
  AddressForm,
  type AddressInput,
} from "@/app/(account)/account/address-form";
import { Alert, Button, Skeleton, TextField } from "@/components/ui";
import styles from "./page.module.css";

export type AddressSelection =
  | { kind: "saved"; addressId: string }
  | {
      kind: "inline";
      address: AddressInput;
      guestEmail?: string;
      guestPhone?: string;
    };

export function AddressStep({
  isAuthenticated,
  accessToken,
  initial,
  onContinue,
}: {
  isAuthenticated: boolean;
  accessToken: string | null;
  initial: AddressSelection | null;
  onContinue: (selection: AddressSelection) => void;
}) {
  const { dict } = useDictionary();
  const t = dict.checkout.address;

  const { data: addresses } = useQuery({
    queryKey: ["my-addresses"],
    queryFn: () => listMyAddresses(accessToken),
    enabled: isAuthenticated,
  });

  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(
    initial?.kind === "saved" ? initial.addressId : null,
  );

  // Pre-select the account's default address once the list loads, so a
  // returning customer with one saved address can just hit Continue —
  // derived at render time rather than synced via an effect, since
  // there's no external system here to synchronize with.
  const effectiveSelectedId =
    selectedAddressId ??
    addresses?.find((a) => a.is_default)?.id ??
    addresses?.[0]?.id ??
    null;
  // Not derived from `addresses` at mount: that query is still loading
  // on first render (`addresses` is undefined), so baking its length
  // into a useState initializer would permanently lock this to "true"
  // before the list ever has a chance to arrive. Whether to show the
  // saved list or the form is instead decided per-render below, once
  // `addresses` has actually loaded.
  const [useNew, setUseNew] = useState(
    !isAuthenticated || initial?.kind === "inline",
  );
  const [guestEmail, setGuestEmail] = useState(
    initial?.kind === "inline" ? (initial.guestEmail ?? "") : "",
  );
  const [guestPhone, setGuestPhone] = useState(
    initial?.kind === "inline" ? (initial.guestPhone ?? "") : "",
  );
  const [error, setError] = useState<string | null>(null);

  function handleSavedContinue() {
    if (!effectiveSelectedId) return;
    onContinue({ kind: "saved", addressId: effectiveSelectedId });
  }

  async function handleInlineSubmit(address: AddressInput) {
    setError(null);
    if (!isAuthenticated && !guestEmail.trim() && !guestPhone.trim()) {
      setError(t.guestHint);
      return;
    }
    onContinue({
      kind: "inline",
      address,
      guestEmail: guestEmail.trim() || undefined,
      guestPhone: guestPhone.trim() || undefined,
    });
  }

  return (
    <div className={styles.stepBody}>
      <h2>{t.heading}</h2>

      {isAuthenticated && addresses === undefined && <Skeleton height="6rem" />}

      {isAuthenticated && !useNew && addresses && addresses.length > 0 && (
        <>
          <span>{t.savedHeading}</span>
          {addresses.map((address: Address) => (
            <label
              key={address.id}
              className={`${styles.optionCard} ${effectiveSelectedId === address.id ? styles.optionCardSelected : ""}`}
            >
              <input
                type="radio"
                name="saved-address"
                checked={effectiveSelectedId === address.id}
                onChange={() => setSelectedAddressId(address.id)}
              />
              <div className={styles.optionCardBody}>
                <span className={styles.optionCardTitle}>
                  {address.label ? `${address.label} — ` : ""}
                  {address.recipient_name}
                </span>
                <span className={styles.optionCardMeta}>
                  {address.address_line1}, {address.city}, {address.district}
                </span>
              </div>
            </label>
          ))}

          <div className={styles.actionsRow}>
            <Button variant="ghost" onClick={() => setUseNew(true)}>
              {t.useNewButton}
            </Button>
            <Button
              disabled={!effectiveSelectedId}
              onClick={handleSavedContinue}
            >
              {dict.checkout.continueButton}
            </Button>
          </div>
        </>
      )}

      {(useNew ||
        !isAuthenticated ||
        (addresses !== undefined && addresses.length === 0)) && (
        <>
          <span>{isAuthenticated ? t.useNewButton : t.guestHeading}</span>

          {!isAuthenticated && (
            <>
              <TextField
                label={t.guestEmailLabel}
                type="email"
                value={guestEmail}
                onChange={(e) => setGuestEmail(e.target.value)}
              />
              <TextField
                label={t.guestPhoneLabel}
                type="tel"
                value={guestPhone}
                onChange={(e) => setGuestPhone(e.target.value)}
              />
              <p style={{ fontSize: "0.85rem", opacity: 0.75 }}>
                {t.guestHint}
              </p>
            </>
          )}

          {error && <Alert tone="danger">{error}</Alert>}

          <AddressForm
            submitLabel={dict.checkout.continueButton}
            onSubmit={handleInlineSubmit}
            onCancel={
              isAuthenticated && addresses && addresses.length > 0
                ? () => setUseNew(false)
                : undefined
            }
          />
        </>
      )}
    </div>
  );
}

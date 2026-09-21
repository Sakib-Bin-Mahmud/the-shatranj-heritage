"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import formStyles from "@/components/form.module.css";
import { AddressForm, type AddressInput } from "./address-form";
import { ProfileForm } from "./profile-form";
import { OrdersTab } from "./orders-tab";
import styles from "./page.module.css";

type Address = AddressInput & { id: string; customer_id: string };
type Tab = "profile" | "addresses" | "orders";

export default function AccountPage() {
  return (
    <Suspense fallback={null}>
      <AccountPageContent />
    </Suspense>
  );
}

function AccountPageContent() {
  const { status, customer, accessToken, refreshProfile } = useAuth();
  const { dict } = useDictionary();
  const t = dict.account;
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab");
  const [tab, setTab] = useState<Tab>(
    initialTab === "addresses" || initialTab === "orders"
      ? initialTab
      : "profile",
  );

  const [addresses, setAddresses] = useState<Address[] | null>(null);
  const [addressesError, setAddressesError] = useState<string | null>(null);
  const [addressesVersion, setAddressesVersion] = useState(0);
  const [addingAddress, setAddingAddress] = useState(false);
  const [editingAddressId, setEditingAddressId] = useState<string | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  useEffect(() => {
    if (status !== "authenticated" || !accessToken) return;

    let cancelled = false;
    apiFetch<Address[]>("/customers/me/addresses", { accessToken })
      .then((data) => {
        if (!cancelled) setAddresses(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setAddressesError(
            err instanceof ApiClientError ? err.message : t.loadError,
          );
        }
      });

    return () => {
      cancelled = true;
    };
    // `t.loadError` intentionally excluded: a locale switch shouldn't
    // re-trigger an address re-fetch, only change which string a
    // *future* failure in this effect would show.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, accessToken, addressesVersion]);

  function reloadAddresses() {
    setAddressesVersion((v) => v + 1);
  }

  async function handleAddAddress(input: AddressInput) {
    await apiFetch("/customers/me/addresses", {
      method: "POST",
      accessToken,
      body: input,
    });
    setAddingAddress(false);
    reloadAddresses();
  }

  async function handleUpdateAddress(id: string, input: AddressInput) {
    await apiFetch(`/customers/me/addresses/${id}`, {
      method: "PATCH",
      accessToken,
      body: input,
    });
    setEditingAddressId(null);
    reloadAddresses();
  }

  async function handleDeleteAddress(id: string) {
    await apiFetch(`/customers/me/addresses/${id}`, {
      method: "DELETE",
      accessToken,
    });
    reloadAddresses();
  }

  if (status !== "authenticated" || !customer) {
    return (
      <div className={styles.page} role="status">
        {dict.common.loading}
      </div>
    );
  }

  function handleTabChange(next: Tab) {
    setTab(next);
    router.replace(`/account?tab=${next}`, { scroll: false });
  }

  return (
    <div className={styles.page}>
      <section className={styles.section}>
        <h1>{t.heading}</h1>
        <p>
          {customer.email ?? customer.mobile_number} · {t.statusLabel}:{" "}
          {customer.status}
        </p>
      </section>

      <nav className={styles.tabs} aria-label="Account sections">
        <button
          type="button"
          className={`${styles.tab} ${tab === "profile" ? styles.tabActive : ""}`}
          onClick={() => handleTabChange("profile")}
        >
          {t.tabs.profile}
        </button>
        <button
          type="button"
          className={`${styles.tab} ${tab === "addresses" ? styles.tabActive : ""}`}
          onClick={() => handleTabChange("addresses")}
        >
          {t.tabs.addresses}
        </button>
        <button
          type="button"
          className={`${styles.tab} ${tab === "orders" ? styles.tabActive : ""}`}
          onClick={() => handleTabChange("orders")}
        >
          {t.tabs.orders}
        </button>
      </nav>

      {tab === "profile" && (
        <section className={styles.section}>
          <h2>{t.profile.heading}</h2>
          <ProfileForm
            customer={customer}
            accessToken={accessToken}
            onSaved={() => refreshProfile()}
          />
        </section>
      )}

      {tab === "orders" && <OrdersTab accessToken={accessToken} />}

      {tab === "addresses" && (
        <section className={styles.section}>
          <h2>{t.addresses.heading}</h2>
          {addressesError && (
            <p className={formStyles.error} role="alert">
              {addressesError}
            </p>
          )}

          {addresses === null ? (
            <p role="status">{t.addresses.loading}</p>
          ) : addresses.length === 0 && !addingAddress ? (
            <p>{t.addresses.empty}</p>
          ) : (
            <ul className={styles.addressList}>
              {addresses.map((address) =>
                editingAddressId === address.id ? (
                  <li key={address.id} className={styles.addressCard}>
                    <AddressForm
                      initial={address}
                      submitLabel={t.addresses.form.saveSubmitLabel}
                      onSubmit={(input) =>
                        handleUpdateAddress(address.id, input)
                      }
                      onCancel={() => setEditingAddressId(null)}
                    />
                  </li>
                ) : (
                  <li key={address.id} className={styles.addressCard}>
                    {address.is_default && (
                      <span className={styles.defaultBadge}>
                        {t.addresses.defaultBadge}
                      </span>
                    )}
                    <strong>{address.recipient_name}</strong>
                    <span>{address.phone}</span>
                    <span>
                      {address.address_line1}
                      {address.address_line2
                        ? `, ${address.address_line2}`
                        : ""}
                    </span>
                    <span>
                      {address.city}, {address.district} {address.postal_code}
                    </span>
                    <div className={styles.addressActions}>
                      <button
                        type="button"
                        onClick={() => setEditingAddressId(address.id)}
                      >
                        {dict.common.edit}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteAddress(address.id)}
                      >
                        {dict.common.delete}
                      </button>
                    </div>
                  </li>
                ),
              )}
            </ul>
          )}

          {addingAddress ? (
            <AddressForm
              submitLabel={t.addresses.form.addSubmitLabel}
              onSubmit={handleAddAddress}
              onCancel={() => setAddingAddress(false)}
            />
          ) : (
            <button type="button" onClick={() => setAddingAddress(true)}>
              {t.addresses.addButton}
            </button>
          )}
        </section>
      )}
    </div>
  );
}

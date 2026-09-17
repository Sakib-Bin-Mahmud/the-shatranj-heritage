"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import formStyles from "@/components/form.module.css";
import { AddressForm, type AddressInput } from "./address-form";
import { ProfileForm } from "./profile-form";
import styles from "./page.module.css";

type Address = AddressInput & { id: string; customer_id: string };

export default function AccountPage() {
  const { status, customer, accessToken, refreshProfile } = useAuth();
  const router = useRouter();

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
            err instanceof ApiClientError
              ? err.message
              : "Could not load addresses.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
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
    return <div className={styles.page}>Loading…</div>;
  }

  return (
    <div className={styles.page}>
      <section className={styles.section}>
        <h1>My account</h1>
        <p>
          {customer.email ?? customer.mobile_number} · Status: {customer.status}
        </p>
      </section>

      <section className={styles.section}>
        <h2>Profile</h2>
        <ProfileForm
          customer={customer}
          accessToken={accessToken}
          onSaved={() => refreshProfile()}
        />
      </section>

      <section className={styles.section}>
        <h2>Delivery addresses</h2>
        {addressesError && <p className={formStyles.error}>{addressesError}</p>}

        {addresses === null ? (
          <p>Loading addresses…</p>
        ) : addresses.length === 0 && !addingAddress ? (
          <p>No saved addresses yet.</p>
        ) : (
          <ul className={styles.addressList}>
            {addresses.map((address) =>
              editingAddressId === address.id ? (
                <li key={address.id} className={styles.addressCard}>
                  <AddressForm
                    initial={address}
                    submitLabel="Save address"
                    onSubmit={(input) => handleUpdateAddress(address.id, input)}
                    onCancel={() => setEditingAddressId(null)}
                  />
                </li>
              ) : (
                <li key={address.id} className={styles.addressCard}>
                  {address.is_default && (
                    <span className={styles.defaultBadge}>Default</span>
                  )}
                  <strong>{address.recipient_name}</strong>
                  <span>{address.phone}</span>
                  <span>
                    {address.address_line1}
                    {address.address_line2 ? `, ${address.address_line2}` : ""}
                  </span>
                  <span>
                    {address.city}, {address.district} {address.postal_code}
                  </span>
                  <div className={styles.addressActions}>
                    <button
                      type="button"
                      onClick={() => setEditingAddressId(address.id)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteAddress(address.id)}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ),
            )}
          </ul>
        )}

        {addingAddress ? (
          <AddressForm
            submitLabel="Add address"
            onSubmit={handleAddAddress}
            onCancel={() => setAddingAddress(false)}
          />
        ) : (
          <button type="button" onClick={() => setAddingAddress(true)}>
            Add address
          </button>
        )}
      </section>
    </div>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import type { Customer } from "@/lib/auth-context";
import formStyles from "@/components/form.module.css";

export function ProfileForm({
  customer,
  accessToken,
  onSaved,
}: {
  customer: Customer;
  accessToken: string | null;
  onSaved: () => Promise<void>;
}) {
  // Rendered only once `customer` is loaded (see account/page.tsx), so
  // this initializer reflects the real profile on first mount without
  // needing an effect to sync it in afterwards.
  const [fullName, setFullName] = useState(customer.full_name);
  const [preferredLanguage, setPreferredLanguage] = useState(
    customer.preferred_language ?? "en",
  );
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSaving(true);
    try {
      await apiFetch("/customers/me", {
        method: "PATCH",
        accessToken,
        body: { full_name: fullName, preferred_language: preferredLanguage },
      });
      await onSaved();
      setMessage("Profile updated.");
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Could not update profile.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className={formStyles.form} onSubmit={handleSubmit}>
      <label>
        Full name
        <input
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </label>
      <label>
        Preferred language
        <select
          value={preferredLanguage}
          onChange={(e) => setPreferredLanguage(e.target.value)}
        >
          <option value="en">English</option>
          <option value="bn">বাংলা</option>
        </select>
      </label>
      {error && <p className={formStyles.error}>{error}</p>}
      {message && <p className={formStyles.success}>{message}</p>}
      <button type="submit" disabled={saving}>
        {saving ? "Saving…" : "Save profile"}
      </button>
    </form>
  );
}

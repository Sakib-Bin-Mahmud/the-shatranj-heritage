"use client";

import { useState, type FormEvent } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import type { Customer } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
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
  const { dict } = useDictionary();
  const t = dict.account.profile;
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
      setMessage(t.successMessage);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t.genericError);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className={formStyles.form} onSubmit={handleSubmit}>
      <label>
        {dict.auth.register.fullNameLabel}
        <input
          required
          autoComplete="name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </label>
      <label>
        {t.preferredLanguageLabel}
        <select
          value={preferredLanguage}
          onChange={(e) => setPreferredLanguage(e.target.value)}
        >
          <option value="en">{t.optionEnglish}</option>
          <option value="bn">{t.optionBangla}</option>
        </select>
      </label>
      {error && (
        <p className={formStyles.error} role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className={formStyles.success} role="status">
          {message}
        </p>
      )}
      <button type="submit" disabled={saving}>
        {saving ? dict.common.saving : t.submit}
      </button>
    </form>
  );
}

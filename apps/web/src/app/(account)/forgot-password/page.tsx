"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import { useDictionary } from "@/i18n/dictionary-context";
import styles from "@/components/form.module.css";

export default function ForgotPasswordPage() {
  const { dict } = useDictionary();
  const t = dict.auth.forgotPassword;
  const [identifier, setIdentifier] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [debugToken, setDebugToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setDebugToken(null);
    setSubmitting(true);
    try {
      const data = await apiFetch<{ debug_reset_token?: string } | null>(
        "/auth/forgot-password",
        {
          method: "POST",
          body: { identifier },
        },
      );
      setMessage(t.successMessage);
      if (data?.debug_reset_token) {
        // Stopgap until a real email/SMS vendor is wired behind the
        // notification service — see
        // apps/api/app/modules/notifications/providers.py. Only ever
        // present when the API runs with DEBUG=true.
        setDebugToken(data.debug_reset_token);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t.genericError);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>{t.heading}</h1>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label>
          {t.identifierLabel}
          <input
            type="text"
            required
            autoComplete="username"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />
        </label>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {message && (
          <p className={styles.success} role="status">
            {message}
          </p>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? t.submitting : t.submit}
        </button>
      </form>

      {debugToken && (
        <p className={styles.hint}>
          {t.devModeHint}{" "}
          <Link
            href={`/reset-password?token=${encodeURIComponent(debugToken)}`}
          >
            {t.resetLink}
          </Link>
          .
        </p>
      )}

      <p className={styles.hint}>
        <Link href="/login">{dict.common.backToLogin}</Link>
      </p>
    </div>
  );
}

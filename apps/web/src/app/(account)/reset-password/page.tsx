"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import { useDictionary } from "@/i18n/dictionary-context";
import styles from "@/components/form.module.css";

function ResetPasswordForm() {
  const { dict } = useDictionary();
  const t = dict.auth.resetPassword;
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState(searchParams.get("token") ?? "");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch("/auth/reset-password", {
        method: "POST",
        body: { token, new_password: newPassword },
      });
      setSuccess(true);
      setTimeout(() => router.push("/login"), 1500);
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
          {t.tokenLabel}
          <input
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
        </label>

        <label>
          {t.newPasswordLabel}
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </label>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {success && (
          <p className={styles.success} role="status">
            {t.successMessage}
          </p>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? t.submitting : t.submit}
        </button>
      </form>
      <p className={styles.hint}>
        <Link href="/login">{dict.common.backToLogin}</Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}

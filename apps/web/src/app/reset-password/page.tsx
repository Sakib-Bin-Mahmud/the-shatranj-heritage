"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import styles from "@/components/form.module.css";

function ResetPasswordForm() {
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
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Could not reset password.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Reset password</h1>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label>
          Reset token
          <input
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
        </label>

        <label>
          New password
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </label>

        {error && <p className={styles.error}>{error}</p>}
        {success && (
          <p className={styles.success}>
            Password reset. Redirecting to login…
          </p>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? "Resetting…" : "Reset password"}
        </button>
      </form>
      <p className={styles.hint}>
        <Link href="/login">Back to login</Link>
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

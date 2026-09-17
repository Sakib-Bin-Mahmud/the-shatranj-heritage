"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { apiFetch, ApiClientError } from "@/lib/api-client";
import styles from "@/components/form.module.css";

export default function ForgotPasswordPage() {
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
      setMessage(
        "If that account exists, password reset instructions have been sent.",
      );
      if (data?.debug_reset_token) {
        // Stopgap until Phase 7 wires real email/SMS delivery — see
        // apps/api/app/modules/auth/router.py. Only ever present when the
        // API runs with DEBUG=true.
        setDebugToken(data.debug_reset_token);
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Something went wrong.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Forgot password</h1>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label>
          Email or mobile number
          <input
            type="text"
            required
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />
        </label>

        {error && <p className={styles.error}>{error}</p>}
        {message && <p className={styles.success}>{message}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Sending…" : "Send reset instructions"}
        </button>
      </form>

      {debugToken && (
        <p className={styles.hint}>
          Dev mode — no email/SMS provider yet:{" "}
          <Link
            href={`/reset-password?token=${encodeURIComponent(debugToken)}`}
          >
            reset your password
          </Link>
          .
        </p>
      )}

      <p className={styles.hint}>
        <Link href="/login">Back to login</Link>
      </p>
    </div>
  );
}

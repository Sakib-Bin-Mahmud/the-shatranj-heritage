"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import styles from "@/components/form.module.css";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({ identifier, password });
      router.push("/account");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Log in</h1>
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

        <label>
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <p className={styles.error}>{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className={styles.hint}>
        <Link href="/forgot-password">Forgot your password?</Link>
      </p>
      <p className={styles.hint}>
        New here? <Link href="/register">Create an account</Link>
      </p>
    </div>
  );
}

"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ApiClientError } from "@/lib/api-client";
import { useAdminAuth } from "@/lib/admin-auth-context";
import styles from "@/components/form.module.css";

export default function AdminLoginPage() {
  const { status, login } = useAdminAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.push("/admin");
  }, [status, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({ email, password });
      router.push("/admin");
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Could not sign in.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Shatranj Admin</h1>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            required
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>

        <label>
          Password
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

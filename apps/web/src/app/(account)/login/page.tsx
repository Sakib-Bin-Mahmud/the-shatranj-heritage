"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import styles from "@/components/form.module.css";

export default function LoginPage() {
  const { login } = useAuth();
  const { dict } = useDictionary();
  const t = dict.auth.login;
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

        <label>
          {dict.common.password}
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
          {submitting ? t.submitting : dict.common.logIn}
        </button>
      </form>
      <p className={styles.hint}>
        <Link href="/forgot-password">{t.forgotLink}</Link>
      </p>
      <p className={styles.hint}>
        {t.newHere} <Link href="/register">{t.createAccountLink}</Link>
      </p>
    </div>
  );
}

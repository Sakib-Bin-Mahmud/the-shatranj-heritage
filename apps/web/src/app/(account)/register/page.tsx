"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import styles from "@/components/form.module.css";

type IdentifierMode = "email" | "mobile";

export default function RegisterPage() {
  const { register } = useAuth();
  const { dict } = useDictionary();
  const t = dict.auth.register;
  const router = useRouter();

  const [mode, setMode] = useState<IdentifierMode>("email");
  const [identifier, setIdentifier] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({
        email: mode === "email" ? identifier : undefined,
        mobile_number: mode === "mobile" ? identifier : undefined,
        password,
        full_name: fullName,
      });
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
          {t.fullNameLabel}
          <input
            type="text"
            required
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </label>

        <label>
          {t.registerWithLabel}
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as IdentifierMode)}
          >
            <option value="email">{t.optionEmail}</option>
            <option value="mobile">{t.optionMobile}</option>
          </select>
        </label>

        <label>
          {mode === "email" ? t.emailLabel : t.mobileLabel}
          <input
            type={mode === "email" ? "email" : "tel"}
            required
            autoComplete={mode === "email" ? "email" : "tel"}
            placeholder={mode === "mobile" ? t.mobilePlaceholder : undefined}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />
        </label>

        <label>
          {dict.common.password}
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <p className={styles.hint}>{t.passwordHint}</p>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? t.submitting : t.submit}
        </button>
      </form>
      <p className={styles.hint}>
        {t.haveAccount} <Link href="/login">{dict.common.logIn}</Link>
      </p>
    </div>
  );
}

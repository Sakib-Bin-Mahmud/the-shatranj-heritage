"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import styles from "@/components/form.module.css";

type IdentifierMode = "email" | "mobile";

export default function RegisterPage() {
  const { register } = useAuth();
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
      setError(
        err instanceof ApiClientError ? err.message : "Registration failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Create an account</h1>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label>
          Full name
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </label>

        <label>
          Register with
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as IdentifierMode)}
          >
            <option value="email">Email</option>
            <option value="mobile">Mobile number</option>
          </select>
        </label>

        <label>
          {mode === "email" ? "Email address" : "Mobile number"}
          <input
            type={mode === "email" ? "email" : "tel"}
            required
            placeholder={mode === "mobile" ? "01XXXXXXXXX" : undefined}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
          />
        </label>

        <label>
          Password
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <p className={styles.hint}>
          At least 8 characters, with a letter and a digit.
        </p>

        {error && <p className={styles.error}>{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className={styles.hint}>
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </div>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useDictionary } from "@/i18n/dictionary-context";
import { subscribeToNewsletter } from "@/lib/api/newsletter";
import { ApiClientError } from "@/lib/api-client";
import styles from "./home.module.css";

export function NewsletterSection() {
  const { dict } = useDictionary();
  const t = dict.home;
  const [email, setEmail] = useState("");
  const mutation = useMutation({
    mutationFn: (value: string) => subscribeToNewsletter(value),
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate(email);
  }

  return (
    <section className={styles.newsletter}>
      <h2 className={styles.newsletterHeading}>{t.newsletterHeading}</h2>
      <p className={styles.newsletterBody}>{t.newsletterBody}</p>

      {mutation.isSuccess ? (
        <p
          className={`${styles.newsletterFeedback} ${styles.newsletterFeedbackSuccess}`}
          role="status"
        >
          {t.newsletterSuccessMessage}
        </p>
      ) : (
        <form className={styles.newsletterForm} onSubmit={handleSubmit}>
          <label
            htmlFor="newsletter-email"
            className={styles.newsletterVisuallyHiddenLabel}
          >
            {dict.auth.register.emailLabel}
          </label>
          <input
            id="newsletter-email"
            type="email"
            required
            autoComplete="email"
            placeholder={t.newsletterPlaceholder}
            className={styles.newsletterInput}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            type="submit"
            className={styles.newsletterSubmit}
            disabled={mutation.isPending}
          >
            {mutation.isPending
              ? t.newsletterSubmitting
              : t.newsletterSubmitButton}
          </button>
        </form>
      )}

      {mutation.isError && (
        <p
          className={`${styles.newsletterFeedback} ${styles.newsletterFeedbackError}`}
          role="alert"
        >
          {mutation.error instanceof ApiClientError
            ? mutation.error.message
            : dict.common.genericError}
        </p>
      )}
    </section>
  );
}

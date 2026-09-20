"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { subscribeToNewsletter } from "@/lib/api/newsletter";
import { ApiClientError } from "@/lib/api-client";
import styles from "./home.module.css";

export function NewsletterSection() {
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
      <h2 className={styles.newsletterHeading}>Join the Circle</h2>
      <p className={styles.newsletterBody}>
        New collections, artisan stories, and quiet announcements — sent rarely,
        and never without reason.
      </p>

      {mutation.isSuccess ? (
        <p
          className={`${styles.newsletterFeedback} ${styles.newsletterFeedbackSuccess}`}
          role="status"
        >
          You&rsquo;re in. Welcome to the circle.
        </p>
      ) : (
        <form className={styles.newsletterForm} onSubmit={handleSubmit}>
          <label
            htmlFor="newsletter-email"
            className={styles.newsletterVisuallyHiddenLabel}
          >
            Email address
          </label>
          <input
            id="newsletter-email"
            type="email"
            required
            placeholder="your@email.com"
            className={styles.newsletterInput}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            type="submit"
            className={styles.newsletterSubmit}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Subscribing…" : "Subscribe"}
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
            : "Something went wrong. Please try again."}
        </p>
      )}
    </section>
  );
}

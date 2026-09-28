import { apiFetch } from "@/lib/api-client";

export type NewsletterSubscription = {
  email: string;
  is_active: boolean;
};

export function subscribeToNewsletter(
  email: string,
): Promise<NewsletterSubscription> {
  return apiFetch<NewsletterSubscription>("/newsletter/subscribe", {
    method: "POST",
    body: { email },
  });
}

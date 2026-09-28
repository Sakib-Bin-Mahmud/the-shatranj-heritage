const STORAGE_KEY = "shatranj_guest_order_contact";

/**
 * The email/phone a guest used at checkout, stashed just before
 * `placeOrder` so the confirmation page — reached only after a full
 * browser redirect through the payment gateway, which drops all
 * in-memory state — can still look the order up via
 * `GET /orders/guest/{order_number}`. Never put this in the
 * redirect URL itself: that would leak it to the gateway and to
 * browser history.
 */
export function setGuestOrderContact(contact: string): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, contact);
  } catch {
    // Ignore storage failures (private browsing, quota, etc.).
  }
}

export function getGuestOrderContact(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

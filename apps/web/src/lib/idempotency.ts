const STORAGE_KEY = "shatranj_checkout_idempotency_key";

/**
 * A stable key for the current checkout attempt, persisted in
 * sessionStorage so a retry (network blip, double-click, page
 * reload after a redirect) reuses the same key instead of minting a
 * new one — that's what makes the backend's Idempotency-Key replay
 * protection (NFR-REL-001) actually reachable from the UI. Call
 * `resetIdempotencyKey` once an order is successfully placed so the
 * *next* checkout attempt gets a fresh key.
 */
export function getOrCreateIdempotencyKey(): string {
  if (typeof window === "undefined") return crypto.randomUUID();
  try {
    const existing = sessionStorage.getItem(STORAGE_KEY);
    if (existing) return existing;
    const fresh = crypto.randomUUID();
    sessionStorage.setItem(STORAGE_KEY, fresh);
    return fresh;
  } catch {
    return crypto.randomUUID();
  }
}

export function resetIdempotencyKey(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore storage failures (private browsing, quota, etc.).
  }
}

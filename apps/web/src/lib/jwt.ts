// Decodes a JWT's payload without verifying its signature — fine for
// reading claims already trusted because they came straight from our
// own API's login/refresh response, purely to drive UI (nav gating,
// expiry-aware refresh timing). The server independently re-verifies
// and re-checks permissions on every request, so a forged or stale
// claim here can't grant access to anything.
export function decodeJwtPayload<T = Record<string, unknown>>(
  token: string,
): T | null {
  const segment = token.split(".")[1];
  if (!segment) return null;
  try {
    const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      "=",
    );
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as T;
  } catch {
    return null;
  }
}

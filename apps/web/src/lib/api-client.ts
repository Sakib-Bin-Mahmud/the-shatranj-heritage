import { apiBaseUrl } from "./env";

export class ApiClientError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = "ApiClientError";
  }
}

type ApiEnvelope<T> =
  | { success: true; message: string; data: T }
  | { success: false; error: { code: string; message: string } };

type FetchOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  accessToken?: string | null;
  headers?: Record<string, string>;
};

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { method = "GET", body, accessToken, headers: extraHeaders } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extraHeaders,
  };
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
      method,
      headers,
      // The API runs on a different origin in dev (NEXT_PUBLIC_API_URL),
      // so the guest cart session cookie (see lib/api/cart.ts) needs
      // "include" explicitly — the fetch default omits credentials on
      // cross-origin requests.
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiClientError(
      "NETWORK_ERROR",
      "Could not reach the server. Please try again.",
    );
  }

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    // No JSON body (e.g. a 204) — leave payload null.
  }

  if (!response.ok || !payload || payload.success === false) {
    const code =
      (payload && !payload.success && payload.error.code) || "UNKNOWN_ERROR";
    const rawMessage =
      payload && !payload.success ? payload.error.message : undefined;
    // Validation errors carry a list of per-field issues rather than a
    // plain string (see app/core/responses.py validation_exception_handler).
    const message =
      typeof rawMessage === "string"
        ? rawMessage
        : rawMessage
          ? "Please check the highlighted fields and try again."
          : "Something went wrong.";
    throw new ApiClientError(code, message);
  }

  return payload.data;
}

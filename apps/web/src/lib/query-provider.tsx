"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { ApiClientError } from "./api-client";

function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiClientError && error.code !== "NETWORK_ERROR") {
    // A well-formed API error (validation, not-found, forbidden, ...)
    // won't succeed on retry — only network failures are transient.
    return false;
  }
  return failureCount < 2;
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: shouldRetry,
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: false,
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

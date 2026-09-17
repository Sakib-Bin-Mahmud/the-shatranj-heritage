"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { apiFetch } from "./api-client";

const REFRESH_TOKEN_KEY = "shatranj_refresh_token";

export type Customer = {
  id: string;
  email: string | null;
  mobile_number: string | null;
  full_name: string;
  preferred_language?: string;
  status?: string;
};

type TokenPair = { access_token: string; refresh_token: string };

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  customer: Customer | null;
  accessToken: string | null;
  status: AuthStatus;
  register: (input: {
    email?: string;
    mobile_number?: string;
    password: string;
    full_name: string;
  }) => Promise<void>;
  login: (input: { identifier: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: (token?: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeRefreshToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) localStorage.setItem(REFRESH_TOKEN_KEY, token);
    else localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // Ignore storage failures (private browsing, quota, etc.).
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  // Always "loading" on first render, matching the static/server-rendered
  // shell (which has no access to localStorage). Reading the stored
  // refresh token here instead would make the very first client render
  // diverge from what was server-rendered whenever a token IS present,
  // which is a hydration mismatch (React error #418) — so that check
  // belongs in the effect below, post-hydration, not in this initializer.
  const [status, setStatus] = useState<AuthStatus>("loading");

  const clearSession = useCallback(() => {
    storeRefreshToken(null);
    setCustomer(null);
    setAccessToken(null);
    setStatus("unauthenticated");
  }, []);

  const applySession = useCallback((tokens: TokenPair, profile: Customer) => {
    storeRefreshToken(tokens.refresh_token);
    setAccessToken(tokens.access_token);
    setCustomer(profile);
    setStatus("authenticated");
  }, []);

  const refreshProfile = useCallback(
    async (token?: string) => {
      const activeToken = token ?? accessToken;
      if (!activeToken) return;
      const profile = await apiFetch<Customer>("/customers/me", {
        accessToken: activeToken,
      });
      setCustomer(profile);
    },
    [accessToken],
  );

  // Access tokens are kept in memory only (not localStorage) so every
  // fresh page load exercises the refresh-token flow, per the Phase 1
  // exit criteria in docs/Implementation Plan.md ("verify session
  // persists via refresh token").
  useEffect(() => {
    const storedRefreshToken = readStoredRefreshToken();
    if (!storedRefreshToken) {
      // Reading localStorage — an external system, not render-available
      // data — so setting state here (rather than during render) is the
      // correct place for it, despite what a generic "no setState in
      // effects" lint heuristic might suggest.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStatus("unauthenticated");
      return;
    }

    apiFetch<TokenPair>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: storedRefreshToken },
    })
      .then(async (tokens) => {
        storeRefreshToken(tokens.refresh_token);
        setAccessToken(tokens.access_token);
        const profile = await apiFetch<Customer>("/customers/me", {
          accessToken: tokens.access_token,
        });
        setCustomer(profile);
        setStatus("authenticated");
      })
      .catch(() => clearSession());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const register = useCallback<AuthContextValue["register"]>(
    async (input) => {
      const data = await apiFetch<{ customer: Customer } & TokenPair>(
        "/auth/register",
        {
          method: "POST",
          body: input,
        },
      );
      applySession(data, data.customer);
    },
    [applySession],
  );

  const login = useCallback<AuthContextValue["login"]>(
    async (input) => {
      const data = await apiFetch<{ customer: Customer } & TokenPair>(
        "/auth/login",
        {
          method: "POST",
          body: input,
        },
      );
      applySession(data, data.customer);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    const refreshToken = readStoredRefreshToken();
    if (refreshToken) {
      try {
        await apiFetch("/auth/logout", {
          method: "POST",
          body: { refresh_token: refreshToken },
        });
      } catch {
        // Best-effort — clear local session regardless.
      }
    }
    clearSession();
  }, [clearSession]);

  return (
    <AuthContext.Provider
      value={{
        customer,
        accessToken,
        status,
        register,
        login,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

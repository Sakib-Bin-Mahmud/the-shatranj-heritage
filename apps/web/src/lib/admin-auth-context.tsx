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
import { decodeJwtPayload } from "./jwt";

const ADMIN_REFRESH_TOKEN_KEY = "shatranj_admin_refresh_token";
const ADMIN_PROFILE_KEY = "shatranj_admin_profile";

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
};

type AdminTokenPair = { access_token: string; refresh_token: string };
type AdminAccessClaims = { permissions?: string[] };
type AdminAuthStatus = "loading" | "authenticated" | "unauthenticated";

type AdminAuthContextValue = {
  admin: AdminUser | null;
  accessToken: string | null;
  permissions: string[];
  status: AdminAuthStatus;
  login: (input: { email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (code: string) => boolean;
};

const AdminAuthContext = createContext<AdminAuthContextValue | null>(null);

function readStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(ADMIN_REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeSession(refreshToken: string | null, profile: AdminUser | null) {
  if (typeof window === "undefined") return;
  try {
    if (refreshToken && profile) {
      localStorage.setItem(ADMIN_REFRESH_TOKEN_KEY, refreshToken);
      localStorage.setItem(ADMIN_PROFILE_KEY, JSON.stringify(profile));
    } else {
      localStorage.removeItem(ADMIN_REFRESH_TOKEN_KEY);
      localStorage.removeItem(ADMIN_PROFILE_KEY);
    }
  } catch {
    // Ignore storage failures (private browsing, quota, etc.).
  }
}

function readStoredProfile(): AdminUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(ADMIN_PROFILE_KEY);
    return raw ? (JSON.parse(raw) as AdminUser) : null;
  } catch {
    return null;
  }
}

function permissionsFromAccessToken(accessToken: string): string[] {
  return decodeJwtPayload<AdminAccessClaims>(accessToken)?.permissions ?? [];
}

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  // Always "loading" on first render — see the identical note in
  // lib/auth-context.tsx: reading localStorage here would diverge from
  // the server-rendered shell and trigger a hydration mismatch.
  const [status, setStatus] = useState<AdminAuthStatus>("loading");

  const clearSession = useCallback(() => {
    storeSession(null, null);
    setAdmin(null);
    setAccessToken(null);
    setPermissions([]);
    setStatus("unauthenticated");
  }, []);

  const applySession = useCallback(
    (tokens: AdminTokenPair, profile: AdminUser) => {
      storeSession(tokens.refresh_token, profile);
      setAccessToken(tokens.access_token);
      setPermissions(permissionsFromAccessToken(tokens.access_token));
      setAdmin(profile);
      setStatus("authenticated");
    },
    [],
  );

  // Mirrors the customer session's own refresh-once-at-mount pattern
  // (see lib/auth-context.tsx): the access token lives in memory only,
  // so every fresh page load re-derives it from the stored refresh
  // token via the shared /auth/refresh endpoint (it accepts either
  // token type). There's no GET /admin/auth/me endpoint to re-fetch a
  // fresh profile, so the admin summary captured at login/refresh time
  // is persisted alongside the refresh token instead.
  useEffect(() => {
    const storedRefreshToken = readStoredRefreshToken();
    const storedProfile = readStoredProfile();
    if (!storedRefreshToken || !storedProfile) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStatus("unauthenticated");
      return;
    }

    apiFetch<AdminTokenPair>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: storedRefreshToken },
    })
      .then((tokens) => {
        applySession(tokens, storedProfile);
      })
      .catch(() => clearSession());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback<AdminAuthContextValue["login"]>(
    async (input) => {
      const data = await apiFetch<{ admin: AdminUser } & AdminTokenPair>(
        "/admin/auth/login",
        { method: "POST", body: input },
      );
      applySession(data, data.admin);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    const refreshToken = readStoredRefreshToken();
    if (refreshToken) {
      try {
        await apiFetch("/admin/auth/logout", {
          method: "POST",
          body: { refresh_token: refreshToken },
        });
      } catch {
        // Best-effort — clear local session regardless.
      }
    }
    clearSession();
  }, [clearSession]);

  const hasPermission = useCallback(
    (code: string) => permissions.includes(code),
    [permissions],
  );

  return (
    <AdminAuthContext.Provider
      value={{
        admin,
        accessToken,
        permissions,
        status,
        login,
        logout,
        hasPermission,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth(): AdminAuthContextValue {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error("useAdminAuth must be used within an AdminAuthProvider");
  }
  return context;
}

import type { ReactNode } from "react";
import { AdminAuthProvider } from "@/lib/admin-auth-context";

// Only the auth context lives here — /admin/login has no sidebar, and
// the internal design-preview page needs neither auth nor the shell.
// The sidebar chrome and its auth gate live in admin/(shell)/layout.tsx,
// applied only to the routes that need it.
export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminAuthProvider>{children}</AdminAuthProvider>;
}

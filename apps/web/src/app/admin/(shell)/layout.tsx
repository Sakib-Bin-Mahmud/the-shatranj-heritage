import type { ReactNode } from "react";
import { AdminShell } from "@/components/admin-sidebar-nav";

// Every route under this group requires a logged-in admin — AdminShell
// itself (a client component, since auth state only exists client-side)
// redirects to /admin/login when unauthenticated and renders the
// permission-gated sidebar otherwise.
export default function AdminShellLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <AdminShell>{children}</AdminShell>;
}

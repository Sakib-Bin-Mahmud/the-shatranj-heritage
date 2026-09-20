import type { ReactNode } from "react";
import { AdminShell } from "@/components/admin-sidebar-nav";

// RBAC enforcement (redirecting non-staff away, gating nav links by
// permission) lands in Phase F5 alongside admin auth — this shell only
// establishes the visual/structural layout per Phase F0's scope.
export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}

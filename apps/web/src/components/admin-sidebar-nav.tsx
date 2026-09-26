"use client";

import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAdminAuth } from "@/lib/admin-auth-context";
import { titleCaseList } from "@/lib/text-format";
import styles from "./admin-sidebar-nav.module.css";

// English-only by design (see docs/Frontend Implementation Plan.md §2:
// "i18n" row) — the Admin Portal is a staff tool, not a customer
// surface, so it isn't wired to DictionaryProvider.
//
// `permission` gates whether the link renders at all — a role sees
// only the sections its permissions cover (Phase F5 exit criteria).
// Dashboard has none: it's the universal landing page every staff
// account gets after login, its own content adapts to what the viewer
// can see. Each other permission code matches exactly what the
// corresponding admin endpoint requires server-side (see each
// module's router.py `require_permission(...)`), so this list is a
// visibility mirror of real access, not a separate access-control
// decision.
type NavLink = {
  href: string;
  label: string;
  // A link with more than one code is visible if the admin has ANY of
  // them (e.g. Content covers both category management and CMS pages,
  // gated on separate permission codes that content_manager holds
  // together but which are, in principle, independently grantable).
  permission?: string | string[];
};

function linkVisible(
  link: NavLink,
  hasPermission: (code: string) => boolean,
): boolean {
  if (!link.permission) return true;
  const codes = Array.isArray(link.permission)
    ? link.permission
    : [link.permission];
  return codes.some(hasPermission);
}

const NAV_GROUPS: {
  label: string;
  links: NavLink[];
}[] = [
  {
    label: "Overview",
    links: [{ href: "/admin", label: "Dashboard" }],
  },
  {
    label: "Catalog",
    links: [
      {
        href: "/admin/products",
        label: "Products",
        permission: "products.write",
      },
      {
        href: "/admin/inventory",
        label: "Inventory",
        permission: "inventory.read",
      },
      {
        href: "/admin/content",
        label: "Content",
        permission: ["categories.write", "cms.write"],
      },
    ],
  },
  {
    label: "Commerce",
    links: [
      // Shipping (courier assignment, delivery progression) lives inside
      // each order's own detail page rather than as its own section —
      // see app/admin/(shell)/orders/[orderId]/shipment-section.tsx —
      // so there is no separate "/admin/shipping" route to link here.
      { href: "/admin/orders", label: "Orders", permission: "orders.read" },
      {
        href: "/admin/customers",
        label: "Customers",
        permission: "customers.read",
      },
    ],
  },
  {
    label: "Insights",
    links: [
      { href: "/admin/reports", label: "Reports", permission: "reports.read" },
    ],
  },
  {
    label: "Administration",
    links: [
      {
        href: "/admin/staff",
        label: "Staff & Roles",
        permission: "staff.manage",
      },
      {
        href: "/admin/audit-logs",
        label: "Audit Log",
        permission: "audit.read",
      },
      {
        href: "/admin/settings",
        label: "Settings",
        permission: "settings.manage",
      },
    ],
  },
];

export function accessibleLinks(
  hasPermission: (code: string) => boolean,
): { href: string; label: string }[] {
  return NAV_GROUPS.flatMap((group) =>
    group.links.filter(
      (link) => link.href !== "/admin" && linkVisible(link, hasPermission),
    ),
  );
}

function AdminSidebar() {
  const { admin, permissions, hasPermission, logout } = useAdminAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/admin/login");
  }

  return (
    <aside className={styles.sidebar}>
      <Link href="/admin" className={styles.brand}>
        Shatranj Admin
      </Link>
      <nav className={styles.nav}>
        {NAV_GROUPS.map((group) => {
          const visibleLinks = group.links.filter((link) =>
            linkVisible(link, hasPermission),
          );
          if (visibleLinks.length === 0) return null;
          return (
            <div key={group.label} className={styles.navGroup}>
              <div className={styles.navGroupLabel}>{group.label}</div>
              {visibleLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={styles.navLink}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          );
        })}
      </nav>
      <div className={styles.account}>
        {admin && (
          <>
            <span className={styles.accountName}>{admin.full_name}</span>
            <span className={styles.accountRoles}>
              {admin.roles.length > 0
                ? titleCaseList(admin.roles)
                : "No role assigned"}
            </span>
          </>
        )}
        {permissions.length === 0 && (
          <span className={styles.accountRoles}>No permissions granted</span>
        )}
        <button
          type="button"
          className={styles.logoutButton}
          onClick={handleLogout}
        >
          Log out
        </button>
      </div>
    </aside>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const { status } = useAdminAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") router.push("/admin/login");
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div className={styles.loadingShell} role="status">
        {status === "loading" ? "Loading…" : null}
      </div>
    );
  }

  return (
    <div className={styles.shell}>
      <AdminSidebar />
      <div className={styles.content}>{children}</div>
    </div>
  );
}

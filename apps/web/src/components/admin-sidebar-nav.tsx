import type { ReactNode } from "react";
import Link from "next/link";
import styles from "./admin-sidebar-nav.module.css";

// English-only by design (see docs/Frontend Implementation Plan.md §2:
// "i18n" row) — the Admin Portal is a staff tool, not a customer
// surface, so it isn't wired to DictionaryProvider.
const NAV_GROUPS: {
  label: string;
  links: { href: string; label: string }[];
}[] = [
  {
    label: "Overview",
    links: [{ href: "/admin", label: "Dashboard" }],
  },
  {
    label: "Catalog",
    links: [
      { href: "/admin/products", label: "Products" },
      { href: "/admin/inventory", label: "Inventory" },
      { href: "/admin/content", label: "Content" },
    ],
  },
  {
    label: "Commerce",
    links: [
      { href: "/admin/orders", label: "Orders" },
      { href: "/admin/customers", label: "Customers" },
      { href: "/admin/shipping", label: "Shipping" },
    ],
  },
  {
    label: "Insights",
    links: [{ href: "/admin/reports", label: "Reports" }],
  },
  {
    label: "Administration",
    links: [
      { href: "/admin/staff", label: "Staff & Roles" },
      { href: "/admin/audit-logs", label: "Audit Log" },
      { href: "/admin/settings", label: "Settings" },
    ],
  },
];

export function AdminShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <Link href="/admin" className={styles.brand}>
          Shatranj Admin
        </Link>
        <nav className={styles.nav}>
          {NAV_GROUPS.map((group) => (
            <div key={group.label} className={styles.navGroup}>
              <div className={styles.navGroupLabel}>{group.label}</div>
              {group.links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={styles.navLink}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      <div className={styles.content}>{children}</div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import styles from "./nav-bar.module.css";

export function NavBar() {
  const { status, customer, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className={styles.header}>
      <Link href="/" className={styles.brand}>
        The Shatranj Heritage
      </Link>
      <nav className={styles.nav}>
        {status === "authenticated" ? (
          <>
            <Link href="/account">{customer?.full_name ?? "Account"}</Link>
            <button
              type="button"
              onClick={handleLogout}
              className={styles.linkButton}
            >
              Log out
            </button>
          </>
        ) : status === "unauthenticated" ? (
          <>
            <Link href="/login">Log in</Link>
            <Link href="/register">Register</Link>
          </>
        ) : null}
      </nav>
    </header>
  );
}

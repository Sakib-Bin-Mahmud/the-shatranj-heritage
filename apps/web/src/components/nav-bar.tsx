"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import styles from "./nav-bar.module.css";

export function NavBar() {
  const { status, customer, logout } = useAuth();
  const { dict, locale, setLocale } = useDictionary();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className={styles.header}>
      <Link href="/" className={styles.brand}>
        {dict.common.siteName}
      </Link>
      <nav className={styles.nav}>
        {status === "authenticated" ? (
          <>
            <Link href="/account">
              {customer?.full_name ?? dict.common.account}
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className={styles.linkButton}
            >
              {dict.common.logOut}
            </button>
          </>
        ) : status === "unauthenticated" ? (
          <>
            <Link href="/login">{dict.common.logIn}</Link>
            <Link href="/register">{dict.common.register}</Link>
          </>
        ) : null}
        <button
          type="button"
          onClick={() => setLocale(locale === "en" ? "bn" : "en")}
          className={styles.linkButton}
        >
          {locale === "en"
            ? dict.nav.localeToggleToBangla
            : dict.nav.localeToggleToEnglish}
        </button>
      </nav>
    </header>
  );
}

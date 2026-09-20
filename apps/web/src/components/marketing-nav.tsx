"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import styles from "./marketing-nav.module.css";

export function MarketingNav() {
  const { status, customer } = useAuth();
  const { dict, locale, setLocale } = useDictionary();

  return (
    <header className={styles.header}>
      <Link href="/" className={styles.brand}>
        ♔ {dict.common.siteName}
      </Link>
      <nav className={styles.nav}>
        {status === "authenticated" ? (
          <Link href="/account">
            {customer?.full_name ?? dict.common.account}
          </Link>
        ) : (
          <>
            <Link href="/login">{dict.common.logIn}</Link>
            <Link href="/register">{dict.common.register}</Link>
          </>
        )}
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

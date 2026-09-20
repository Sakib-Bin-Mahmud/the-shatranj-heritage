"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth-context";
import { useDictionary } from "@/i18n/dictionary-context";
import { getCart } from "@/lib/api/cart";
import styles from "./storefront-nav.module.css";

export function StorefrontNav() {
  const { status, customer, accessToken } = useAuth();
  const { dict, locale, setLocale } = useDictionary();

  // Guest carts resolve via an httpOnly cookie the API manages itself,
  // so this fetch works logged out too — no accessToken required.
  const { data: cart } = useQuery({
    queryKey: ["cart", accessToken ?? "guest"],
    queryFn: () => getCart(accessToken),
    enabled: status !== "loading",
  });

  return (
    <header className={styles.header}>
      <Link href="/" className={styles.brand}>
        {dict.common.siteName}
      </Link>
      <nav className={styles.nav}>
        <Link href="/products">{dict.nav.shop}</Link>
        {status === "authenticated" ? (
          <Link href="/account">
            {customer?.full_name ?? dict.common.account}
          </Link>
        ) : (
          <Link href="/login">{dict.common.logIn}</Link>
        )}
        <Link href="/cart" className={styles.cartLink}>
          {dict.nav.cart}
          <span className={styles.cartCount}>{cart?.item_count ?? 0}</span>
        </Link>
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

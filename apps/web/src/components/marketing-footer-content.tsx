"use client";

import Link from "next/link";
import { useDictionary } from "@/i18n/dictionary-context";
import type { PageSummary } from "@/lib/api/content";
import styles from "./marketing-footer.module.css";

export function MarketingFooterContent({
  legalPages,
}: {
  legalPages: PageSummary[];
}) {
  const { dict } = useDictionary();

  return (
    <footer className={styles.footer}>
      <div className={styles.top}>
        <div className={styles.brandColumn}>
          <span className={styles.brand}>{dict.common.siteName}</span>
          <span className={styles.tagline}>{dict.common.tagline}</span>
        </div>

        {legalPages.length > 0 && (
          <div className={styles.linkColumn}>
            <span className={styles.columnLabel}>
              {dict.common.footerSupport}
            </span>
            {legalPages.map((page) => (
              <Link
                key={page.slug}
                href={`/legal/${page.slug}`}
                className={styles.footerLink}
              >
                {page.title}
              </Link>
            ))}
          </div>
        )}
      </div>

      <p className={styles.copyright}>
        © {new Date().getFullYear()} {dict.common.siteName}.{" "}
        {dict.common.allRightsReserved}
      </p>
    </footer>
  );
}

import Link from "next/link";
import { getDictionary } from "@/i18n/get-dictionary";
import { defaultLocale } from "@/i18n/config";
import { listContentPages } from "@/lib/api/content";
import styles from "./marketing-footer.module.css";

export async function MarketingFooter() {
  const dict = await getDictionary(defaultLocale);

  // Best-effort: the footer shouldn't break the whole page if the API
  // happens to be unreachable when this server component renders.
  const legalPages = await listContentPages().catch(() => []);

  return (
    <footer className={styles.footer}>
      <div className={styles.top}>
        <div className={styles.brandColumn}>
          <span className={styles.brand}>{dict.common.siteName}</span>
          <span className={styles.tagline}>{dict.common.tagline}</span>
        </div>

        {legalPages.length > 0 && (
          <div className={styles.linkColumn}>
            <span className={styles.columnLabel}>Support</span>
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
        © {new Date().getFullYear()} {dict.common.siteName}. All rights
        reserved.
      </p>
    </footer>
  );
}

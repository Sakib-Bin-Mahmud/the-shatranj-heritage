import { getDictionary } from "@/i18n/get-dictionary";
import { defaultLocale } from "@/i18n/config";
import styles from "./marketing-footer.module.css";

export async function MarketingFooter() {
  const dict = await getDictionary(defaultLocale);

  return (
    <footer className={styles.footer}>
      <p className={styles.glyphRow} aria-hidden="true">
        ♔ ♛ ♜ ♝ ♞ ♟
      </p>
      <p>
        {dict.common.siteName} — {dict.common.tagline}
      </p>
    </footer>
  );
}

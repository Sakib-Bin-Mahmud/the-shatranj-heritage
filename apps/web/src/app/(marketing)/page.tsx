import { getDictionary } from "@/i18n/get-dictionary";
import { defaultLocale } from "@/i18n/config";
import { ApiStatus } from "@/components/api-status";
import styles from "./page.module.css";

export default async function Home() {
  const dict = await getDictionary(defaultLocale);

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>{dict.home.heading}</h1>
        <p>{dict.home.subheading}</p>
        <ApiStatus
          labels={{
            label: dict.home.apiStatusLabel,
            ok: dict.home.apiStatusOk,
            error: dict.home.apiStatusError,
          }}
        />
      </main>
    </div>
  );
}

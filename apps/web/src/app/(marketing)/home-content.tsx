"use client";

import { useDictionary } from "@/i18n/dictionary-context";
import { GrandCollection } from "./grand-collection";
import { NewsletterSection } from "./newsletter-section";
import styles from "./home.module.css";

export function HomeContent() {
  const { dict } = useDictionary();
  const t = dict.home;

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroGrid} aria-hidden="true" />
        <div className={styles.heroVignette} aria-hidden="true" />
        <span className={styles.heroGlyph} aria-hidden="true">
          ♔
        </span>
        <div className={styles.heroContent}>
          <span className={styles.eyebrow}>{t.eyebrow}</span>
          <h1 className={styles.heroHeading}>{t.heroHeading}</h1>
          <p className={styles.heroSubheading}>{t.heroSubheading}</p>
          <a href="#grand-collection" className={styles.ctaButton}>
            {t.heroCta}
          </a>
        </div>
      </section>

      <section className={styles.masters}>
        <div className={styles.mastersPortrait}>
          <span className={styles.mastersPortraitLabel}>
            {t.artisanPortraitLabel}
          </span>
        </div>
        <div className={styles.mastersBody}>
          <span className={styles.mastersEyebrow}>{t.mastersEyebrow}</span>
          <p className={styles.mastersQuote}>&ldquo;{t.mastersQuote}&rdquo;</p>
          <span className={styles.mastersAttribution}>
            {t.mastersAttribution}
          </span>
          <div className={styles.mastersBadgeRow}>
            <span className={styles.mastersBadgeSeal} aria-hidden="true">
              ♔
            </span>
            <span className={styles.mastersBadgeLabel}>
              {t.mastersBadgeLabel}
            </span>
          </div>
        </div>
      </section>

      <GrandCollection
        eyebrow={t.collectionEyebrow}
        title={t.collectionTitle}
        emptyMessage={t.collectionEmpty}
        viewPieceLabel={t.viewPieceLink}
      />

      <section className={styles.oath}>
        <div className={styles.oathItem}>
          <span className={styles.oathGlyph} aria-hidden="true">
            ♔
          </span>
          <span className={styles.oathTitle}>{t.oathTitle1}</span>
          <p className={styles.oathBody}>{t.oathBody1}</p>
        </div>
        <div className={styles.oathItem}>
          <span className={styles.oathGlyph} aria-hidden="true">
            ♖
          </span>
          <span className={styles.oathTitle}>{t.oathTitle2}</span>
          <p className={styles.oathBody}>{t.oathBody2}</p>
        </div>
        <div className={styles.oathItem}>
          <span className={styles.oathGlyph} aria-hidden="true">
            ♘
          </span>
          <span className={styles.oathTitle}>{t.oathTitle3}</span>
          <p className={styles.oathBody}>{t.oathBody3}</p>
        </div>
      </section>

      <NewsletterSection />
    </>
  );
}

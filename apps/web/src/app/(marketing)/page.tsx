import type { Metadata } from "next";
import { GrandCollection } from "./grand-collection";
import { NewsletterSection } from "./newsletter-section";
import styles from "./home.module.css";

const description =
  "Handcrafted chess sets, carved by master artisans and bound in stories older than the game itself — Bangladesh's first dedicated home for the noble game.";

// The page itself has no server data (GrandCollection fetches
// client-side), but MarketingFooter's legal-page links are server-fetched
// CMS content — revalidate periodically so a newly published/unpublished
// policy page doesn't wait for the next full rebuild to show up.
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "The Shatranj Heritage — Step Into the Enchanted Chess Hall",
  description,
  openGraph: {
    title: "The Shatranj Heritage",
    description,
    type: "website",
    siteName: "The Shatranj Heritage",
  },
  twitter: {
    card: "summary_large_image",
    title: "The Shatranj Heritage",
    description,
  },
};

export default function Home() {
  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroGrid} aria-hidden="true" />
        <div className={styles.heroVignette} aria-hidden="true" />
        <span className={styles.heroGlyph} aria-hidden="true">
          ♔
        </span>
        <div className={styles.heroContent}>
          <span className={styles.eyebrow}>An Enchanted Collection</span>
          <h1 className={styles.heroHeading}>
            Step Into the Enchanted Chess Hall
          </h1>
          <p className={styles.heroSubheading}>
            Handcrafted chess sets, carved by master artisans and bound in
            stories older than the game itself — Bangladesh&rsquo;s first
            dedicated home for the noble game.
          </p>
          <a href="#grand-collection" className={styles.ctaButton}>
            Explore the Collection
          </a>
        </div>
      </section>

      <section className={styles.masters}>
        <div className={styles.mastersPortrait}>
          <span className={styles.mastersPortraitLabel}>
            [Artisan Portrait]
          </span>
        </div>
        <div className={styles.mastersBody}>
          <span className={styles.mastersEyebrow}>Masters of the Craft</span>
          <p className={styles.mastersQuote}>
            &ldquo;Every board holds a hundred small decisions — the grain, the
            weight, the balance of a knight in your hand.&rdquo;
          </p>
          <span className={styles.mastersAttribution}>
            — Abdul Karim, Master Woodcarver, Dhaka
          </span>
          <div className={styles.mastersBadgeRow}>
            <span className={styles.mastersBadgeSeal} aria-hidden="true">
              ♔
            </span>
            <span className={styles.mastersBadgeLabel}>
              Handcrafted in Bangladesh
            </span>
          </div>
        </div>
      </section>

      <GrandCollection />

      <section className={styles.oath}>
        <div className={styles.oathItem}>
          <span className={styles.oathGlyph} aria-hidden="true">
            ♔
          </span>
          <span className={styles.oathTitle}>Authentic Craftsmanship</span>
          <p className={styles.oathBody}>
            Every piece is made by hand — no two boards are ever quite the same.
          </p>
        </div>
        <div className={styles.oathItem}>
          <span className={styles.oathGlyph} aria-hidden="true">
            ♖
          </span>
          <span className={styles.oathTitle}>Heritage of Bangladesh</span>
          <p className={styles.oathBody}>
            Built in trust with local artisan workshops, generation after
            generation.
          </p>
        </div>
        <div className={styles.oathItem}>
          <span className={styles.oathGlyph} aria-hidden="true">
            ♘
          </span>
          <span className={styles.oathTitle}>Certified Quality</span>
          <p className={styles.oathBody}>
            Each set is inspected and guaranteed before it ever reaches your
            door.
          </p>
        </div>
      </section>

      <NewsletterSection />
    </>
  );
}

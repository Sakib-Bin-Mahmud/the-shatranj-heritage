import type { HTMLAttributes, ReactNode } from "react";
import styles from "./card.module.css";

export type CardProps = HTMLAttributes<HTMLDivElement> & {
  title?: string;
  actions?: ReactNode;
  // Defaults to "h3" for a Card nested under a section's own h2. Pages
  // whose h1 is followed directly by Card titles (no h2 in between,
  // e.g. the admin dashboard and reports stat cards) should pass "h2"
  // so the heading outline doesn't skip a level.
  headingLevel?: "h2" | "h3" | "h4";
};

export function Card({
  title,
  actions,
  headingLevel: HeadingTag = "h3",
  className,
  children,
  ...rest
}: CardProps) {
  return (
    <div
      className={[styles.card, className].filter(Boolean).join(" ")}
      {...rest}
    >
      {(title || actions) && (
        <div className={styles.header}>
          {title && <HeadingTag className={styles.title}>{title}</HeadingTag>}
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}

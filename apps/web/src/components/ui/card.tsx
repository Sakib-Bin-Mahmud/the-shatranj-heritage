import type { HTMLAttributes, ReactNode } from "react";
import styles from "./card.module.css";

export type CardProps = HTMLAttributes<HTMLDivElement> & {
  title?: string;
  actions?: ReactNode;
};

export function Card({
  title,
  actions,
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
          {title && <h3 className={styles.title}>{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}

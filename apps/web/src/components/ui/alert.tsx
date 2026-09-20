import type { HTMLAttributes } from "react";
import styles from "./alert.module.css";

export type AlertTone = "info" | "success" | "warning" | "danger";

export type AlertProps = HTMLAttributes<HTMLDivElement> & {
  tone?: AlertTone;
};

// Matches the role="alert"/"status" pattern established in Phase 8:
// danger/warning are assertive (role="alert"), info/success are
// polite (role="status") — a screen reader interrupts for the former,
// announces the latter only once idle.
export function Alert({ tone = "info", className, ...rest }: AlertProps) {
  const role = tone === "danger" || tone === "warning" ? "alert" : "status";

  return (
    <div
      role={role}
      className={[styles.alert, styles[tone], className]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    />
  );
}

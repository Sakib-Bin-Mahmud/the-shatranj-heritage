"use client";

import styles from "./page.module.css";

export type BarItem = {
  key: string;
  label: string;
  value: number;
  displayValue: string;
};

// A small sequential (single-hue, magnitude) bar list for the handful of
// categories reports like "orders by status" or "refunds by status"
// carry — few enough rows that a full axis/gridline chart would be
// overkill, but still comparing magnitude across categories, so one
// hue, sorted descending, with the exact value directly labeled (never
// hidden behind a hover-only tooltip) per the dataviz guidance.
export function ValueBarList({ items }: { items: BarItem[] }) {
  if (items.length === 0) return null;
  const max = Math.max(...items.map((i) => i.value), 1);
  const sorted = [...items].sort((a, b) => b.value - a.value);

  return (
    <div className={styles.barList}>
      {sorted.map((item) => (
        <div key={item.key} className={styles.barRow}>
          <span className={styles.barLabel}>{item.label}</span>
          <div className={styles.barTrack}>
            <div
              className={styles.barFill}
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
          <span className={styles.barValue}>{item.displayValue}</span>
        </div>
      ))}
    </div>
  );
}

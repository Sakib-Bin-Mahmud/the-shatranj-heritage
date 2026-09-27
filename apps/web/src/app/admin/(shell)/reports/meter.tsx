"use client";

import styles from "./page.module.css";

// A single ratio against a 100% limit — the fill is the accent hue, the
// unfilled track is a lighter step of the same ramp, so the value reads
// across the whole bar rather than needing a legend.
export function Meter({ label, percent }: { label: string; percent: number }) {
  const clamped = Math.min(Math.max(percent, 0), 100);
  return (
    <div className={styles.meter}>
      <div className={styles.meterHeader}>
        <span>{label}</span>
        <span className={styles.meterValue}>{percent.toFixed(1)}%</span>
      </div>
      <div className={styles.meterTrack}>
        <div className={styles.meterFill} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}

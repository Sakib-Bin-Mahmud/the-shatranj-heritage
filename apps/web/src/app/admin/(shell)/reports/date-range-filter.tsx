"use client";

import { Button, TextField } from "@/components/ui";
import styles from "./page.module.css";

export type DateRange = { fromDate: string; toDate: string };

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return isoDate(d);
}

const PRESETS: { label: string; days: number }[] = [
  { label: "Last 7 days", days: 7 },
  { label: "Last 30 days", days: 30 },
  { label: "Last 90 days", days: 90 },
];

export function DateRangeFilter({
  range,
  onChange,
}: {
  range: DateRange;
  onChange: (range: DateRange) => void;
}) {
  const today = isoDate(new Date());

  return (
    <div className={styles.filterRow}>
      <div className={styles.presetRow}>
        {PRESETS.map((preset) => (
          <Button
            key={preset.label}
            variant="secondary"
            onClick={() =>
              onChange({ fromDate: daysAgo(preset.days), toDate: today })
            }
          >
            {preset.label}
          </Button>
        ))}
      </div>
      <TextField
        label="From"
        type="date"
        value={range.fromDate}
        max={range.toDate}
        onChange={(e) => onChange({ ...range, fromDate: e.target.value })}
      />
      <TextField
        label="To"
        type="date"
        value={range.toDate}
        min={range.fromDate}
        max={today}
        onChange={(e) => onChange({ ...range, toDate: e.target.value })}
      />
    </div>
  );
}

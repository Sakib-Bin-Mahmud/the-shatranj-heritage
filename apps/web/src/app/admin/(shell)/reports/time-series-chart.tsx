"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import styles from "./page.module.css";

export type TimeSeriesPoint = { period: string; value: number };

function formatPeriodLabel(period: string): string {
  const d = new Date(period);
  if (Number.isNaN(d.getTime())) return period;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function CustomTooltip({
  active,
  payload,
  label,
  valueFormatter,
  seriesLabel,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
  valueFormatter: (value: number) => string;
  seriesLabel: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipDate}>
        {label ? formatPeriodLabel(label) : ""}
      </div>
      <div className={styles.tooltipRow}>
        <span className={styles.tooltipKey} aria-hidden="true" />
        <span className={styles.tooltipLabel}>{seriesLabel}</span>
        <strong className={styles.tooltipValue}>
          {valueFormatter(payload[0].value)}
        </strong>
      </div>
    </div>
  );
}

// A single-series line/area chart — one hue (sequential), no legend box
// needed since there's only one series (the chart title already names
// it). Used for revenue-over-time and customer-growth, which share the
// same "one number per period" shape.
export function TimeSeriesChart({
  data,
  seriesLabel,
  valueFormatter = (v) => v.toLocaleString("en-US"),
}: {
  data: TimeSeriesPoint[];
  seriesLabel: string;
  valueFormatter?: (value: number) => string;
}) {
  if (data.length === 0) {
    return <p className={styles.chartEmpty}>No data in this range.</p>;
  }

  return (
    <div className={styles.chartWrap}>
      {/* Recharts renders an inert SVG with no text content a screen
          reader can use, so the actual data is also exposed as a plain
          table — visually hidden, but the real accessible alternative,
          not just a one-line summary of the trend. */}
      <table className="visually-hidden">
        <caption>{seriesLabel} over time</caption>
        <thead>
          <tr>
            <th scope="col">Period</th>
            <th scope="col">{seriesLabel}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((point) => (
            <tr key={point.period}>
              <td>{formatPeriodLabel(point.period)}</td>
              <td>{valueFormatter(point.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div aria-hidden="true">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart
            data={data}
            margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              vertical={false}
              stroke="var(--border-color)"
              strokeDasharray="0"
            />
            <XAxis
              dataKey="period"
              tickFormatter={formatPeriodLabel}
              tick={{ fill: "var(--foreground)", fontSize: 12 }}
              axisLine={{ stroke: "var(--border-color)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "var(--foreground)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={56}
              tickFormatter={(v: number) => v.toLocaleString("en-US")}
            />
            <Tooltip
              content={
                <CustomTooltip
                  valueFormatter={valueFormatter}
                  seriesLabel={seriesLabel}
                />
              }
            />
            <Area
              type="monotone"
              dataKey="value"
              isAnimationActive={false}
              stroke="var(--color-info)"
              strokeWidth={2}
              fill="var(--color-info)"
              fillOpacity={0.1}
              dot={{ r: 3, fill: "var(--color-info)", strokeWidth: 0 }}
              activeDot={{
                r: 5,
                fill: "var(--color-info)",
                stroke: "var(--surface-0)",
                strokeWidth: 2,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

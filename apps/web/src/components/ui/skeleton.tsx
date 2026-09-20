import type { HTMLAttributes } from "react";
import styles from "./skeleton.module.css";

export type SkeletonProps = HTMLAttributes<HTMLSpanElement> & {
  width?: string | number;
  height?: string | number;
};

export function Skeleton({
  width = "100%",
  height = "1em",
  style,
  className,
  ...rest
}: SkeletonProps) {
  return (
    <span
      aria-hidden="true"
      className={[styles.skeleton, className].filter(Boolean).join(" ")}
      style={{ width, height, ...style }}
      {...rest}
    />
  );
}

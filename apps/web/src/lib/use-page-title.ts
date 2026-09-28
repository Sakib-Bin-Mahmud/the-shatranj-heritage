"use client";

import { useEffect } from "react";

const SITE_NAME = "Shatranj Admin";

// The Admin Portal's routes are all Client Components rendered inside one
// shared root layout with a single static <title>, so navigating between
// them (e.g. /admin/orders to /admin/products) otherwise leaves the
// document title — and anything a screen reader announces from it —
// unchanged. Call this once per page with a short, human name for the
// route.
export function usePageTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} — ${SITE_NAME}`;
  }, [title]);
}

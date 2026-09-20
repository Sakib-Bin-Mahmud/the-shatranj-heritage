"use client";

import { useEffect, useState } from "react";
import { apiBaseUrl } from "@/lib/env";

type Status = "checking" | "ok" | "error";

export function ApiStatus({
  labels,
}: {
  labels: { label: string; ok: string; error: string };
}) {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;

    fetch(`${apiBaseUrl}/health`)
      .then((res) => {
        if (!cancelled) setStatus(res.ok ? "ok" : "error");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <p>
      {labels.label}:{" "}
      <strong data-status={status}>
        {status === "checking"
          ? "…"
          : status === "ok"
            ? labels.ok
            : labels.error}
      </strong>
    </p>
  );
}

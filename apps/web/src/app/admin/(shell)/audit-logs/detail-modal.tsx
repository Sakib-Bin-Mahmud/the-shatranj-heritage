"use client";

import type { AuditLogEntry } from "@/lib/api/audit";
import { Modal } from "@/components/ui";
import styles from "./page.module.css";

export function AuditDetailModal({
  entry,
  onClose,
}: {
  entry: AuditLogEntry | null;
  onClose: () => void;
}) {
  return (
    <Modal
      open={Boolean(entry)}
      onClose={onClose}
      title={entry ? entry.action : "Audit log entry"}
    >
      {entry && (
        <div className={styles.diffColumns}>
          <div className={styles.diffBlock}>
            <span className={styles.diffHeading}>Before</span>
            <pre className={styles.diffPre}>
              {entry.before ? JSON.stringify(entry.before, null, 2) : "—"}
            </pre>
          </div>
          <div className={styles.diffBlock}>
            <span className={styles.diffHeading}>After</span>
            <pre className={styles.diffPre}>
              {entry.after ? JSON.stringify(entry.after, null, 2) : "—"}
            </pre>
          </div>
        </div>
      )}
    </Modal>
  );
}

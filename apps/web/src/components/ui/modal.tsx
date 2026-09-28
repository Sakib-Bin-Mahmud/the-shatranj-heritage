"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import styles from "./modal.module.css";

export type ModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
};

const FOCUSABLE_SELECTOR =
  'input, select, textarea, button, a[href], [tabindex]:not([tabindex="-1"])';

// Built on the native <dialog> element: it gets focus trapping, Escape
// to close, and a backdrop for free, without a new dependency.
export function Modal({ open, onClose, title, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  // The element that had focus right before this modal opened — restored
  // on close so keyboard/screen-reader users land back where they were,
  // not at the top of the document.
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open) {
      if (!dialog.open) {
        triggerRef.current = document.activeElement as HTMLElement | null;
        dialog.showModal();
        // <dialog>'s own autofocus algorithm focuses the dialog itself
        // when nothing carries an `autofocus` attribute, which in
        // practice means the first Tab press lands on the header's
        // close button (the first focusable element in DOM order) —
        // send focus into the actual content instead.
        bodyRef.current
          ?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR)
          ?.focus();
      }
      return () => {
        triggerRef.current?.focus();
        triggerRef.current = null;
      };
    }
    if (dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      className={styles.dialog}
      aria-labelledby={titleId}
      onClose={onClose}
    >
      <div className={styles.header}>
        <h2 id={titleId} className={styles.title}>
          {title}
        </h2>
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close"
        >
          ✕
        </button>
      </div>
      <div className={styles.body} ref={bodyRef}>
        {children}
      </div>
    </dialog>
  );
}

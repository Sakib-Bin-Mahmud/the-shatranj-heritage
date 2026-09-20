import {
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";
import styles from "./field.module.css";

type FieldWrapperProps = {
  label: string;
  hint?: string;
  error?: string;
  id?: string;
  children: (id: string, describedBy: string | undefined) => ReactNode;
};

function FieldWrapper({ label, hint, error, id, children }: FieldWrapperProps) {
  const autoId = useId();
  const fieldId = id ?? autoId;
  const hintId = hint ? `${fieldId}-hint` : undefined;
  const errorId = error ? `${fieldId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={fieldId}>
        {label}
      </label>
      {children(fieldId, describedBy)}
      {hint && (
        <span id={hintId} className={styles.hint}>
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className={styles.errorText} role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export type TextFieldProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "id"
> & {
  label: string;
  hint?: string;
  error?: string;
  id?: string;
};

export function TextField({
  label,
  hint,
  error,
  id,
  className,
  ...rest
}: TextFieldProps) {
  return (
    <FieldWrapper label={label} hint={hint} error={error} id={id}>
      {(fieldId, describedBy) => (
        <input
          id={fieldId}
          className={[styles.control, className].filter(Boolean).join(" ")}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={describedBy}
          {...rest}
        />
      )}
    </FieldWrapper>
  );
}

export type SelectFieldProps = Omit<
  SelectHTMLAttributes<HTMLSelectElement>,
  "id"
> & {
  label: string;
  hint?: string;
  error?: string;
  id?: string;
};

export function SelectField({
  label,
  hint,
  error,
  id,
  className,
  children,
  ...rest
}: SelectFieldProps) {
  return (
    <FieldWrapper label={label} hint={hint} error={error} id={id}>
      {(fieldId, describedBy) => (
        <select
          id={fieldId}
          className={[styles.control, className].filter(Boolean).join(" ")}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={describedBy}
          {...rest}
        >
          {children}
        </select>
      )}
    </FieldWrapper>
  );
}

export type CheckboxFieldProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "id" | "type"
> & {
  label: string;
  id?: string;
};

export function CheckboxField({
  label,
  id,
  className,
  ...rest
}: CheckboxFieldProps) {
  const autoId = useId();
  const fieldId = id ?? autoId;

  return (
    <label htmlFor={fieldId} className={styles.checkboxRow}>
      <input id={fieldId} type="checkbox" className={className} {...rest} />
      {label}
    </label>
  );
}
